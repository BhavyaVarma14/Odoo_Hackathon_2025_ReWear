from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, ValidationError
from models import User, Category

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class ItemUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    size = SelectField('Size', choices=[
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2X Large'),
        ('One Size', 'One Size')
    ], validators=[DataRequired()])
    condition = SelectField('Condition', choices=[
        ('Excellent', 'Excellent - Like new'),
        ('Good', 'Good - Minor wear'),
        ('Fair', 'Fair - Noticeable wear'),
        ('Poor', 'Poor - Significant wear')
    ], validators=[DataRequired()])
    suggested_coin_value = IntegerField('Suggested Coin Value', validators=[DataRequired(), NumberRange(min=1, max=1000)], default=10)
    tags = StringField('Tags (comma separated)', validators=[Length(max=500)])
    images = FileField('Images (select multiple)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Upload Item')
    
    def __init__(self, *args, **kwargs):
        super(ItemUploadForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

class SwapRequestForm(FlaskForm):
    offered_item_id = SelectField('Choose item to offer', coerce=int, validators=[DataRequired()])
    message = TextAreaField('Message (optional)', validators=[Length(max=500)])
    submit = SubmitField('Send Swap Request')
    
    def __init__(self, user_items=None, *args, **kwargs):
        super(SwapRequestForm, self).__init__(*args, **kwargs)
        if user_items:
            self.offered_item_id.choices = [(item.id, f"{item.title} ({item.category.name})") for item in user_items]
        else:
            self.offered_item_id.choices = []

class AdminApprovalForm(FlaskForm):
    coin_value = IntegerField('Coin Value', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    submit = SubmitField('Approve')
    reject = SubmitField('Reject')

class SearchForm(FlaskForm):
    query = StringField('Search items...')
    category_id = SelectField('Category', coerce=lambda x: int(x) if x else None)
    size = SelectField('Size')
    min_coins = IntegerField('Min Coins', validators=[NumberRange(min=0)])
    max_coins = IntegerField('Max Coins', validators=[NumberRange(min=0)])
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [('', 'All Categories')] + [(c.id, c.name) for c in Category.query.all()]
        self.size.choices = [('', 'All Sizes'), ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'), ('One Size', 'One Size')]

class AddressForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    street_address = StringField('Street Address', validators=[DataRequired(), Length(min=5, max=200)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=100)])
    state = StringField('State/Province', validators=[DataRequired(), Length(min=2, max=100)])
    postal_code = StringField('Postal Code', validators=[DataRequired(), Length(min=3, max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Save Address')
