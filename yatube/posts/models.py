from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
CUT = 15


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               )
    group = models.ForeignKey('Group',
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Группы, к которой относится пост',
                              )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:CUT]


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название группы')
    slug = models.SlugField(unique=True, auto_created=True,)
    description = models.TextField(verbose_name='Краткое описание')

    class Meta:
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name="comments",
        on_delete=models.CASCADE
    )
    text = models.TextField(
        verbose_name='Комментарий'
    )
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             verbose_name="Подписчик",
                             related_name='follower',
                             on_delete=models.CASCADE,
                             )
    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE
                               )
