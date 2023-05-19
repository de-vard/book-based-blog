from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.mail import send_mail
from django.db.models import Count

from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from taggit.models import Tag

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def post_list(request, tag_slug=None):
    """Функция не используется, она как пример"""
    posts_list = Post.published.all()

    tag = None
    if tag_slug:  # если передан тег ищем все посты с этим тегом
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__in=[tag])

    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(posts_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number не целое число, то
        # выдать первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number находится вне диапазона, то
        # выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html',
                  {'posts': posts, 'tag': tag, })


class PostListView(ListView):
    """Альтернативное представление списка постов НЕ ИСПОЛЬЗУЕТСЯ"""

    queryset = Post.published.all()  # Используем вместо queryset вместо model=Post, для того что бы не извлекать все
    # объекты Post а только те которые необходимы
    context_object_name = 'posts'
    paginate_by = 3  # пагинация
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    """Детальный просмотр поста"""
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    comments = post.comments.filter(active=True)  # Список активных комментариев к этому посту
    form = CommentForm()  # Форма для комментирования пользователями

    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)  # получаем список тегов которые есть в посте, flat=True,
    # чтобы получить список
    # значение и не список кортежей со значениями
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)  # берутся все посты, содержащие
    # теги, за исключением текущего поста
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(
        request,
        'blog/post/detail.html',
        {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts})


# TODO: в книге используют переменную после отправки что бы просто скрыть форму отправки, мне это не нравиться,
#  используй перенаправление после отправки сообщения
def post_share(request, post_id):
    """Отображение и отправки сообщений"""
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False  # переменная для шаблона, если истина скрывает форму отправки
    if request.method == 'POST':
        # Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data

            # метод request.build_absolute_uri() - формирует полный URL-адрес, включая HTTP-схему и хост-имя
            post_url = request.build_absolute_uri(post.get_absolute_url())  # добавляем ссылку на сам пост

            subject = f"{cd['name']} recommends you read {post.title}"  # заголовок
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"  # сообщение
            send_mail(subject, message, 'krolik.zip@mail.ru', [cd['to']])
            sent = True  # переменная для шаблона, если истина скрывает форму отправки
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


# TODO: Сделай ред директ после отправки комментария
@require_POST  # разрешает только методом POST для этого представления
def post_comment(request, post_id):
    """Создание комментария"""
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None  # если переданные данные формы валидны, то переменная comment будет содержать созданный комментарий

    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)  # создаем объект, но не сохраняем его, чтобы добавлять данные в него
        comment.post = post  # Назначить пост комментарию
        comment.save()  # Сохранить комментарий в базе данных
    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', config='russian', weight='A') + SearchForm('body', config='russian',
                                                                                             weight='B')
            search_query = SearchQuery(query, config='russian')
            results = Post.published.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(rank__gte=0.3).order_by('-rank')
    return render(request, 'blog/post/search.html',
                  {'form': form, 'query': query, 'results': results})
