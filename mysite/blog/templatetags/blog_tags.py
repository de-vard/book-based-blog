import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

from blog.models import Post

register = template.Library()  # для регистрации шаблонных тегов и фильтров приложения


@register.simple_tag
def total_posts():
    """Количество опубликованных постов"""
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    """Отображение последних опубликованных постов"""
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    """Отображение постов с набольшем количеством комментариев"""
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]


@register.filter(name='markdown')
def markdown_format(text):
    """Шаблонный фильтр"""
    return mark_safe(markdown.markdown(text))  # mark_safe, для того чтобы помечать результат как безопасный для
    # прорисовки в шаблоне исходный код HTML
