from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': "Текст поста",
            'group': "Группа",
            'image': 'Изображение'
        }
        help_text = {
            'text': "текст нового поста",
            'group': "группа, к которой будет относится пост",
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text', )

    def clean_text(self):
        old_comment = self.cleaned_data['text']
        comment = self.cleaned_data['text']
        regulation = ['Пушкин', 'Лермонтов']
        for element in range(len(regulation)):
            regulation[element] = regulation[element].upper()
        regulation = set(regulation)
        comment = comment.upper()
        comment = set(comment.split(' '))
        if comment.intersection(regulation):
            raise ValidationError("Forbidden word!")
        return old_comment
