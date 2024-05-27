from flask_wtf import FlaskForm  # type: ignore[import]
from wtforms.fields import DateField, TimeField  # type: ignore[import]
from wtforms import FileField, StringField, BooleanField, SubmitField, IntegerField  # type: ignore[import]
from wtforms.validators import ValidationError, AnyOf, Length, DataRequired, Regexp  # type: ignore[import]


class Aircraft_Form(FlaskForm):
    registration: StringField = StringField('Registration',
                                            validators=[Length(min=3, max=3),
                                                        Regexp('[A-Z]{3}',
                                                               message="Rego is three upper case alpha characters"),
                                                        DataRequired()]
                                            )
    make = StringField('Make')
    pilot_initials = StringField('Pilot_initials or name', validators=[Length(min=2, max=2)])
    normal_pilot = StringField('Normal_pilot')
    acft_class = StringField('Acft_class')
    # heavy = BooleanField('Heavy')
    self_launch = BooleanField('Self_launch')
    submit = SubmitField()


class Tug_Form(FlaskForm):
    registration = StringField('Registration',
                               validators=[Length(min=3, max=3),
                                           Regexp('[A-Z]{3}', message="Rego is three upper case alpha characters"),
                                           DataRequired()], )

    take_off_date = DateField('Take Off Date Time')
    take_off_time = TimeField('TakeOff', format="%H:%M")

class Tug_UpdateForm(FlaskForm):
    sheet_number = IntegerField('Sheet_Number')
    tug = StringField('Registration', validators=[DataRequired(), Length(min=3, max=3),
                                                  Regexp('[a-zA-Z]+', message="Rego is three alpha characters")])
    take_off_date = DateField('Take Off Date')
    take_off_time = TimeField('TakeOff', format="%H:%M")
    landing_time = TimeField('Land Time', format="%H:%M")
    OGN_ht = IntegerField('OGN Receiver Height')
    launch_ht = IntegerField('Billed Launch Height')


class Glider_Flight_InsertForm(FlaskForm):
    flt_class = StringField(label='Flight Category (CLUB, GLIDER)', validators=[AnyOf(["CLUB", "GLIDER", "VISITOR"])])
    pilot_name = StringField('Pilot Initials  or Name', validators=[DataRequired()])
    glider = StringField('Registration', validators=[DataRequired(), Length(min=3, max=3),
                                                     Regexp('[a-zA-Z]+', message="Rego is three alpha characters")])
    heavy = StringField('Heavy? (Y/N)', validators=[DataRequired(), AnyOf(["Y", "N"], message="Either 'Y' or 'N'")])
    take_off_time = StringField('Take Off Time',
                                validators=[Length(min=5, max=5),
                                            Regexp('^[0-9][0-9]:[0-9][0-9]', message="Time is HH:MM"),
                                            DataRequired()])
    ld_time_str = StringField('Landing (hh:mm)', validators=[Length(min=5, max=5),
                                                             Regexp('^[0-9][0-9]:[0-9][0-9]', message="Time is HH:MM"),
                                                             ])


class Glider_Short_InsertForm(FlaskForm):
    pilot_name = StringField('Pilot Initials  or Name', validators=[DataRequired()])
    glider = StringField('Registration', validators=[DataRequired(), Length(min=3, max=3),
                                                     Regexp('[a-zA-Z]+', message="Rego is three alpha characters")])
    glider_take_off = TimeField('Take Off')
    glider_land = TimeField('Land', format="%H:%M")

class Glider_UpdateForm(FlaskForm):


    glider_take_off = TimeField('Take Off')
    glider_land = TimeField('Land', format="%H:%M")
    glider_rego = StringField('Registration', validators=[DataRequired(), Length(min=3, max=3),
                                                          Regexp('[a-zA-Z]+',
                                                                 message="Rego is three alpha characters")])
    pilot_name = StringField('Pilot Initials  or Name', validators=[DataRequired()])
    pilot2_name = StringField('Second Pilot Initials')


class GliderFlight_AddForm(FlaskForm):
    #   sheet_number = IntegerField('Sheet_Number')
    flt_class = StringField(label='Flight Category (CLUB, GLIDER)', validators=[AnyOf(["CLUB", "GLIDER", "VISITOR"])])
    to_date_str = StringField('Date  ', validators=[Length(min=10, max=10),
                                                    Regexp('^[0-9]4-[0-9]2-[0-9]', message="Date is YYYY-MM-DD"),
                                                    ])
    glider_take_off = TimeField('Take Off')
    # to_time_str = StringField('TakeOff (hh:mm)', validators=[Length(min=5, max=5),
    #                                                          Regexp('^[0-9][0-9]:[0-9][0-9]', message="Time is HH:MM"),
    #                                                          ])
    # ld_time_str = StringField('Landing (hh:mm)', validators=[Length(min=5, max=5),
    #                                                          Regexp('^[0-9][0-9]:[0-9][0-9]', message="Time is HH:MM"),
    #                                                          ])
    glider_land = TimeField('Land', format="%H:%M")
    aircraft = StringField('Registration', validators=[DataRequired(), Length(min=3, max=3)])
    pilot_name = StringField('Pilot Initials  or Name', validators=[DataRequired()])
    pilot2_name = StringField('Second Pilot Initials')


class Ops_UpdateForm(FlaskForm):
    sheet_id = IntegerField('Sheet Id', validators=[DataRequired()])
    flying_day = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])


class Ops_Delete_DayForm(FlaskForm):
    flying_day = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])


class Pilot_Form(FlaskForm):
    pilot_initials = StringField('Pilot initials', validators=[Length(min=2, max=2)])
    pilot_name = StringField('Pilot Name')
    email = StringField('Email')
    phone = StringField('Phone')
    club_member = BooleanField('Club Member')
    contact = StringField('Contact')
    submit = SubmitField()
