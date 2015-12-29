from django import forms
class RegisterForm(forms.Form):
    username=forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2=forms.CharField(label='Confirm',widget=forms.PasswordInput)
    def pwd_validate(self,p1,p2):
        return p1==p2
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)