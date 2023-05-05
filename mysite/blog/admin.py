from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status']
    list_filter = ['status', 'created', 'publish', 'author']  # боковая панель фильтрации
    search_fields = ['title', 'body']  # поиск
    prepopulated_fields = {'slug': ('title',)}  # автоматическое заполнение слага
    raw_id_fields = ['author']  # меняем виджет при выборе пользователя (виджет поиска).Это список полей, которые вы
    # хотели бы превратить в Input виджет для a ForeignKey или ManyToManyField
    date_hierarchy = 'publish'  # быстрая фильтрация по датам
    ordering = ['status', 'publish']  # Критерии сортировки по умолчанию. Если это не указано, администратор Django
    # будет использовать порядок модели по умолчанию.
