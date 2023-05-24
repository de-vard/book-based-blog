from django.contrib.sitemaps import Sitemap
from .models import Post


class PostSitemap(Sitemap):
    changefreq = 'weekly'  # частота изменения страниц
    priority = 0.9  # релевантность постов на веб-странице

    def items(self):
        """Набор QuerySet объектов, подлежащих в эту карту сайта"""
        return Post.published.all()

    def lastmod(self, obj):
        """Метод lastmod получает каждый
            возвращаемый методом items()
            объект и возвращает время
            последнего изменения объекта.
        """
        return obj.updated
