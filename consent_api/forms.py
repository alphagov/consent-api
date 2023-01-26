"""Forms for self-service."""
from flask_wtf import FlaskForm
from wtforms import EmailField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import TelField
from wtforms.validators import DataRequired


class SignUpForm(FlaskForm):
    """Form for creating a new account."""

    name = StringField(
        "Full name",
        validators=[DataRequired()],
    )
    email = EmailField(
        "Email address",
        description="Must be from a public sector organisation",
        validators=[DataRequired()],  # TODO email validation?
    )
    phone = TelField(
        "Mobile number",
        description="We'll send you a security code by text message",
        validators=[DataRequired()],  # TODO validation?
    )
    password = PasswordField(
        "Password",
        description="At least 8 characters",
        validators=[DataRequired()],  # TODO password validation
    )


class SignInForm(FlaskForm):
    """Log in form."""

    email = EmailField(
        "Email address",
        validators=[DataRequired()],  # TODO email validation?
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],  # TODO password validation
    )


class ServiceForm(FlaskForm):
    """Service form."""

    domain = StringField(
        "Domain name",
        validators=[DataRequired()],  # TODO domain validation - no /s
    )
