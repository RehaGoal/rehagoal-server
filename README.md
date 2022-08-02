# rehagoal-server

rehagoal-server is the Django-based server component for the rehagoal-webapp.
Currently it provides a REST service for workflow exchange/management.

## Installation

First install all requirements. Python >= 3.6 is required. 
For the `cryptography` package, you might need build dependencies 
(gcc, libffi-dev, openssl-dev, python3-dev and the Rust Toolchain).
See also https://cryptography.io/en/latest/installation/

On alpine (tested on 3.15):
```sh
apk update
apk add git python3 py3-pip build-base linux-headers gcc musl-dev libffi-dev openssl-dev curl python3-dev
# Install Rust Toolchain
(curl https://sh.rustup.rs -sSf | sh -s -- -y)
source $HOME/.cargo/env
```

Or on Ubuntu (tested on 20.04 LTS)
```bash
sudo apt update
sudo apt install -y git python3-pip
```

Clone the repository and `cd` into it.

Install required Python packages:
```bash
pip3 install -U -r requirements.txt
```

Then generate a new secret key for Django (ignore the `FileNotFoundError` regarding `secretkey.txt` at this point):
```bash
python3 manage.py generate_secret_key
```

Afterwards create a database and/or apply all schema migrations:
```bash
python3 manage.py migrate
```

Finally create a superuser for administration:
```bash
python3 manage.py createsuperuser
```

## Run the development server

```bash
python3 manage.py runserver
```

## Run all unit tests
```bash
python3 manage.py test
```

## Production use
- For production, be sure to change `DEBUG` to `False`, and generate a **new secret key**!
- See also https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/
- Use `manage.py check --deploy` for some automated checks, as recommended by the Django documentation.
- Check the permissions of the secret key file
- Have a look at [`settings.py`](rehagoal_server/settings.py): There are some things you should/might want to change.
  - change `DEBUG` to `False`
  - `ALLOWED_HOSTS`: Remove local addresses and add your domain
  - `CORS_ALLOWED_ORIGINS`: Remove local origins and add origins of the deployed `rehagoal-webapp`
  - `DATABASES`: Change to a better suited DBMS (particularly for performance reasons)
  - `django-private-storage` related settings, e.g. you might want to change the storage backend. 
    However, this has not been tested with `rehagoal-server` yet.
    We recommend to keep the files (even if encrypted) under your control for privacy reasons.
    Otherwise metadata can leak to third parties.
  - possibly other settings - take a look at the Django documentation.
- You should ensure that your service is only accessible via TLS connections that are considered secure.
- You should run the application via a production-grade web server, i.e. you should not use the Django testserver!
  We recommend to use [nginx][nginx] and connect Django via WSGI, for example with [uWSGI][uwsgi]. 
  See `rehagoal-webapp` `README.md` for hints regarding the web server configuration.
- Do not reuse a test database in production, as it might contain users with default passwords!

**Note** that the above information **may be outdated** when you read it, therefore you should do your own research and know
what you are doing.

**You are responsible** for running a secure service, including regular updates/patches of the software you are
running, (privacy-preserving) monitoring, incident response etc..

## Privacy & Security
- You need to add your privacy policy/data protection policy in your user-facing application. We recommend to provide an easy-to-read version in addition to a legally binding version. 
- It is recommended not to rely on third party cloud solutions, as you might leak metadata 
  (IP, time, file that is accessed, fact that user uses the app) to them. If you need to use one, make sure that they
  comply with your local data protection laws.
- At the time of writing, `rehagoal-webapp` does not support further management of uploaded workflows. For GDPR compliance
  it should be possible for the user at least to delete (possibly replace) owned uploaded files (intervenability).
  While the API provides this functionality, there is currently no user interface implemented.
- Currently, `rehagoal-webapp` does not provide functionality to list files/workflows that have been shared with the 
  server. For GDPR compliance it should be possible for the user to get a list of workflows they shared (transparency).
  The API already  implements this: `GET /workflows` returns a list of owned workflows of the authorized user.  
  A view for this information would need to be implemented in `rehagoal-webapp` as well.
- Old files are currently not automatically deleted, same goes for unused user accounts. You might want to change that
  for compliance with local laws.
- While currently the maximum upload size is limited (`200 MiB`), there is no storage quota per user account in place.
  This may need to be added for a deployment in production (availability).
- While `rehagoal-webapp` uploads data end-to-end encrypted to `rehagoal-server` (not just TLS, but also so that the 
  server provider is unable to read the workflow contents), it is not guaranteed that all uploads are actually 
  end-to-end encrypted (the API can be used to upload arbitrary files).
- There is currently no rate limit in place for the API, you might want to add it for production use (availability).
- It is recommended to minimize the amount of information (data minimization) that is acquired from users.
  - Use randomly generated usernames (pseudonyms), for unlinkability with other services.
  - Do not acquire email addresses from users, or use alias addresses that are only used for your service (unlinkability).
  - Do not rely on single sign-on (SSO) solutions of third parties, as they leak metadata.
  - Do not track the user's activity.
  - Reduce the amount of information captured in logfiles to a minimum (as required to ensure a secure/stable service).
  - Do not require the use of an online service by the user. Provide them with options to use the 
    application (`rehagoal-webapp`) in a decentralized or offline way.
- IDs are generated randomly (e.g. User IDs, Filenames, Workflow IDs) to make it more difficult to enumerate them via
  brute force. Currently, IDs are generated as a string of alphanumeric characters (62 symbols) of length 12. This is approximately
  equivalent to $\log_{2}(62^{12}) \approx 71 \text{ bits}$ of information. You might want to increase this number, for example IDs could be instead based on UUIDv4, i.e. 122 bits. Larger numbers of bits means that it is harder to find IDs in use via brute force attacks. However, also the length of the URL and size of the QR code will increase.
  If you change this aspect, make sure to adjust the relevant URL pattern for filenames, as well as server import related
  code in `rehagoal-webapp` (client) to match this change, including the relevant test cases.
- Ideas for the future:
  - Unlinkability could be further improved by not storing the owner with the workflow, but instead allowing the owner of a 
    workflow to prove ownership in zero-knowledge manner. Regarding per-user storage quota, this however also means that a
    privacy-preserving concepts needs to be developed. Authentication could be replaced with anonymous/attribute-based
    credentials, such that workflows are not trivially linkable to a certain user anymore. To show the user a list of
    shared workflows, the client application could remember uploaded workflows. Another possibility would be to store
    this information encrypted on the server, such that it could be synchronized with multiple clients of the same user
    given knowledge of a secret (e.g. password).
  - Unlinkability could be further improved by storing workflows in chunks (at a performance cost), which need to be linked by
    the client application. This makes it harder to know how large a workflow/upload actually is. 
    The client could also upload/download fake chunks to make it more difficult to know which chunks are part of the 
    upload (though repeated queries might give enough information). In a static database scenario though, it would be
    difficult to find corresponding chunks (given that the chunks do not include other metadata).
  - Currently, everyone with an account and the download link can retrieve and decrypt an upload. In the future a more
    sophisticated permission system may be useful. An idea could be to use (decentralized) Attribute-based Encryption
    (ABE), where every user or organization could be their own authority, providing certain attributes. However, this
    requires a well-designed user-interface, concepts for validating ownership of keys and attributes, and most
    importantly it needs to be understood and usable by the actual users.


[uwsgi]: https://uwsgi-docs.readthedocs.io/en/latest/
[nginx]: https://nginx.org/en/