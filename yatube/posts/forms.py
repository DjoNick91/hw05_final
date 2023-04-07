from django.forms import ModelForm, ValidationError
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if 'text' == '':
            raise ValidationError('Пост не может быть пустым!')
        return data


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if 'text' == '':
            raise ValidationError('Комментарий не может быть пустым!')
        return data
