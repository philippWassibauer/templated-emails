===============
templated-emails
===============

This app abstracts the sending of emails in a way so that it is possible to switch from plain text emails to html emails, even if you are using third party apps. 
It does this by using a very similar mechanism as django-notifications. Each email gets a folder. In this folder one can put short.txt (for the subject), email.txt (for the plain text email) and optionally email.html (if an HTML email should also be sent).

A good practice is to put all emails in an emails/ folder within your templates folder, so it is easy to see what emails are being sent by your system.

Sending an emails works like this::

    from templated_emails.utils import send_templated_email
    send_templated_email(["phil@maptales.com"], "emails/invite_friends", {"my_variable":"blafoo"})