from django.db import models

from db.database.model_base import SchemaModel


class User(SchemaModel):
    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1

    STATUS_CHOICES = (
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_ACTIVE, "Active")
    )

    user_id = models.AutoField(db_column='UserID', primary_key=True)
    customer_id = models.IntegerField(db_column='CustomerID', blank=True, null=True)
    user_name = models.CharField(db_column='UserName', max_length=50, blank=True, unique=True)
    name = models.CharField(db_column='Name', max_length=50, default='')
    first_name = models.CharField(db_column='FirstName', max_length=50, blank=True)
    last_name = models.CharField(db_column='LastName', max_length=50, blank=True)
    email = models.CharField(db_column='Email', max_length=100)
    address1 = models.CharField(max_length=50, blank=True)
    address2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip = models.CharField(max_length=16, blank=True)
    country = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    status = models.IntegerField(default=1, choices=STATUS_CHOICES)
    primary_contact = models.IntegerField(db_column='primaryContact', blank=True, null=True)
    admin = models.IntegerField(blank=True, null=True)
    job_title = models.CharField(db_column='JobTitle', max_length=100, blank=True)
    linked_in = models.CharField(db_column='LinkedIn', max_length=200, blank=True)
    twitter = models.CharField(db_column='Twitter', max_length=200, blank=True)
    face_book = models.CharField(db_column='FaceBook', max_length=100, blank=True)
    picture = models.BinaryField(db_column='Picture', blank=True, null=True)
    bio = models.TextField(db_column='Bio', blank=True)
    salutation = models.CharField(db_column='Salutation', max_length=50, blank=True)
    letter_closing = models.CharField(db_column='LetterClosing', max_length=50, blank=True)
    crypt_password = models.BinaryField(db_column='CryptPassword', blank=True, null=True)
    hashed_key = models.BinaryField(db_column='HashedKey', blank=True, null=True)
    password_size = models.IntegerField(db_column='PasswordSize', blank=True, null=True)
    profile_picture = models.URLField(db_column='ProfilePicture', blank=True, null=True, default='')
    roles = models.ManyToManyField(to='Roles', through='UserRole')
    cookie_consent = models.BooleanField(db_column='CookieConsent', default=False)
    cookie_consent_date = models.DateTimeField(db_column='CookieConsentDate', blank=True, null=True)

    @classmethod
    def get_current(cls, using='default', request=None):
        if not using or not request:
            raise Exception('must provide a database and current request')

        user = User.objects.using(using).get(user_name=request.user.user_name)

        return user

    def __get_attribute(self, attribute_name):
        attribute = self.attributes.filter(name=attribute_name).first()
        if not attribute:
            return None
        else:
            return attribute.value

    def get_attribute(self, attribute_name, return_format='string'):
        value = self.__get_attribute(attribute_name)

        if value:
            try:
                if return_format == 'string':
                    return value
                elif return_format == 'int':
                    return int(value)
                elif return_format == 'bool':
                    vl = value.lower()
                    return True if vl in ['1', 'true'] else False
                else:
                    return value
            except:
                return value
        return ''

    def has_role(self, role_name):
        return self.roles.all().filter(name=role_name).exists()

    def __repr__(self):
        return "%s : %s : %s %s" % (self.user_id, self.email, self.first_name, self.last_name)

    class Meta(SchemaModel.Meta):
        # managed = True
        db_table = 'Users'
