import io
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from api.notifications.models import *
from django.db.models import Q, Count, Sum
from weasyprint import HTML
from django.template.loader import get_template
from collections import defaultdict


def compose_email(to_email, template_data, extra_data):
    """
    :param to_email:
    :param template_data:
    :param extra_data:
    :return: True/False
    """
    try:
        domain_id = int(template_data['domain_id']) if "domain_id" in template_data and template_data['domain_id'] != "" else None
        slug = template_data['slug']
        notification_template = NotificationTemplate.objects.filter(Q(event__slug=slug) & Q(site=domain_id) & Q(status=1)).first()
        if notification_template is None:
            notification_template = NotificationTemplate.objects.filter(Q(event__slug=slug) & Q(site__isnull=True) & Q(status=1)).first()
        if notification_template is not None:
            return send_email(to_email, notification_template.id, extra_data)
        return False
    except Exception as exp:
        return False  


def send_email(to_email, template_id, extra_data):
    """
    Send email
    :param to_email:
    :param template_id:
    :param extra_data:
    :return: True/False
    """
    try:
        extra_data['web_url'] = settings.FRONT_BASE_URL
        template_data = get_templates(template_id)
        # -----------------Check template---------------
        if not template_data:
            return "Template not exist."
        # ----------------Set value----------------
        if 'subject' in extra_data and extra_data['subject']:
            subject =  extra_data['subject']
        else:
            subject = template_data.email_subject
        content = template_data.email_content
        # ------------------Dynamic content-----------
        formated_data = defaultdict(lambda: "")
        formated_data.update(extra_data)
        content = content.format_map(formated_data)
        # ----------------Logo----------------
        if "domain_id" in extra_data and extra_data['domain_id'] != "":
            custom_site_settings = CustomSiteSettings.objects.filter(domain_id=int(extra_data['domain_id']), settings_name="website_logo", is_active=1).first()
            if custom_site_settings is not None:
                if custom_site_settings.setting_value is not None and int(custom_site_settings.setting_value) > 0:
                    user_uploads = UserUploads.objects.filter(id=int(custom_site_settings.setting_value), is_active=1).first()
                    if user_uploads is not None:
                        logo = settings.AWS_URL + user_uploads.bucket_name + "/" + user_uploads.doc_file_name
                    else:
                        logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"
                else:
                    logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"
            else:
                logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"

            user_business_profile = UserBusinessProfile.objects.filter(user__site=extra_data['domain_id']).first()
            support_email = user_business_profile.email if user_business_profile is not None else ""
            support_contact_no = user_business_profile.mobile_no if user_business_profile is not None else ""
        else:
            # logo = settings.FRONT_BASE_URL + "/static/images/logo.png"
            support_email = SiteSetting.objects.filter(slug="support_email", is_active=1).first()
            support_contact_no = SiteSetting.objects.filter(slug="support_contact_no", is_active=1).first()
            support_email = support_email.setting_value if support_email is not None else ""
            support_contact_no = support_contact_no.setting_value if support_contact_no is not None else ""
            logo = settings.FRONT_BASE_URL + "/static/images/bidhom_logo_white.png"

        render_data = {"template_message_body": content, "web_url": settings.FRONT_BASE_URL, "logo": logo,
                       "support_email": support_email, "support_contact_no": support_contact_no}
        # --------------------Render email template--------------
        html_content = render_to_string('email/email_header_footer.html', render_data)

        # ----------------Set From Email Text----------------
        from_email_text = settings.FROM_EMAIL_TEXT
        if "domain_id" in extra_data and extra_data['domain_id'] != "":
            network_domain = NetworkDomain.objects.filter(id=extra_data['domain_id']).first()
            if network_domain is not None and network_domain.domain_name:
                from_email_text = network_domain.domain_name.title() + "<noreply@bidhom.com>"

        # ---------------------Send email---------------
        # mail = EmailMultiAlternatives(subject, html_content, settings.FROM_EMAIL_TEXT, to_email)
        mail = EmailMultiAlternatives(subject, html_content, from_email_text, to_email)
        # mail.attach_alternative(html_content, "text/html")
        mail.content_subtype = "html"
        mail.send()
        return True
    except Exception as exp:
        return False


def send_custom_email(to_email, template_id, subject, message=None, extra=None, attachment=None):
    """
    Send email
    :param to_email:
    :param template_id:
    :param subject:
    :param message:
    :param extra:
    :param attachment:
    :return: True/False
    """
    try:
        template_data = get_templates(template_id)
        # -----------------Check template---------------
        if not template_data:
            return "Template not exist."
        # ----------------Set value----------------
        content = template_data.email_content

        # ------------------Dynamic content-----------
        if extra is not None:
            content = content.format(**extra)
        else:
            content = content.format(message=message)

        # ----------------Logo----------------
        if "domain_id" in extra and extra['domain_id'] != "":
            custom_site_settings = CustomSiteSettings.objects.filter(domain_id=int(extra['domain_id']), settings_name="website_logo", is_active=1).first()
            if custom_site_settings is not None:
                if custom_site_settings.setting_value is not None and int(custom_site_settings.setting_value) > 0:
                    user_uploads = UserUploads.objects.filter(id=int(custom_site_settings.setting_value), is_active=1).first()
                    if user_uploads is not None:
                        logo = settings.AWS_URL + user_uploads.bucket_name + "/" + user_uploads.doc_file_name
                    else:
                        logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"
                else:
                    logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"
            else:
                logo = settings.FRONT_BASE_URL + "/static/images/default_img.svg"
        else:
            logo = settings.FRONT_BASE_URL + "/static/images/logo.png"

        render_data = {"template_message_body": content, "web_url": settings.FRONT_BASE_URL, "logo": logo}
        # --------------------Render email template--------------
        html_content = render_to_string('email/email_header_footer.html', render_data)
        # -----------------Attachment------------------
        if attachment is not None:
            html_string = render_to_string('email/loi.html', attachment)
            html = HTML(string=html_string)
            buffer = io.BytesIO()
            html.write_pdf(target=buffer)
            pdf = buffer.getvalue()
            filename = 'offer.pdf'
            mimetype_pdf = 'application/pdf'

        # ---------------------Send email---------------
        mail = EmailMultiAlternatives(subject, content, settings.FROM_EMAIL_TEXT, to_email)
        mail.attach_alternative(html_content, "text/html")
        # -----------------Attachment------------------
        if attachment is not None:
            mail.attach(filename, pdf, mimetype_pdf)
        mail.send()
        return True
    except Exception as exp:
        return False


def get_templates(template_id):
    try:
        notification_template = NotificationTemplate.objects.get(id=template_id)
        return notification_template
    except Exception as exp:
        return False