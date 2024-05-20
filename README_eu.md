<!--
Ohart ongi: README hau automatikoki sortu da <https://github.com/YunoHost/apps/tree/master/tools/readme_generator>ri esker
EZ editatu eskuz.
-->

# Django Example YunoHost-erako

[![Integrazio maila](https://dash.yunohost.org/integration/django_example.svg)](https://dash.yunohost.org/appci/app/django_example) ![Funtzionamendu egoera](https://ci-apps.yunohost.org/ci/badges/django_example.status.svg) ![Mantentze egoera](https://ci-apps.yunohost.org/ci/badges/django_example.maintain.svg)

[![Instalatu Django Example YunoHost-ekin](https://install-app.yunohost.org/install-with-yunohost.svg)](https://install-app.yunohost.org/?app=django_example)

*[Irakurri README hau beste hizkuntzatan.](./ALL_README.md)*

> *Pakete honek Django Example YunoHost zerbitzari batean azkar eta zailtasunik gabe instalatzea ahalbidetzen dizu.*  
> *YunoHost ez baduzu, kontsultatu [gida](https://yunohost.org/install) nola instalatu ikasteko.*

## Aurreikuspena

[![tests](https://github.com/YunoHost-Apps/django_example_ynh/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/YunoHost-Apps/django_example_ynh/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/django_example_ynh/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/django_example_ynh)
[![django_example_ynh @ PyPi](https://img.shields.io/pypi/v/django_example_ynh?label=django_example_ynh%20%40%20PyPi)](https://pypi.org/project/django_example_ynh/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django_example_ynh)](https://github.com/YunoHost-Apps/django_example_ynh/blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/django_example_ynh)](https://github.com/YunoHost-Apps/django_example_ynh/blob/main/LICENSE)

Demo YunoHost Application to demonstrate the integration of a Django project under YunoHost.

Pull requests welcome ;)

This package for YunoHost used [django-yunohost-integration](https://github.com/YunoHost-Apps/django_yunohost_integration)


**Paketatutako bertsioa:** 0.2.0~ynh3
## Dokumentazioa eta baliabideak

- Erabiltzaileen dokumentazio ofiziala: <https://github.com/jedie/django-example>
- Administratzaileen dokumentazio ofiziala: <https://github.com/YunoHost-Apps/django_example_ynh>
- Jatorrizko aplikazioaren kode-gordailua: <https://github.com/YunoHost-Apps/django_example_ynh>
- YunoHost Denda: <https://apps.yunohost.org/app/django_example>
- Eman errore baten berri: <https://github.com/YunoHost-Apps/django_example_ynh/issues>

## Garatzaileentzako informazioa

Bidali `pull request`a [`testing` abarrera](https://github.com/YunoHost-Apps/django_example_ynh/tree/testing).

`testing` abarra probatzeko, ondorengoa egin:

```bash
sudo yunohost app install https://github.com/YunoHost-Apps/django_example_ynh/tree/testing --debug
edo
sudo yunohost app upgrade django_example -u https://github.com/YunoHost-Apps/django_example_ynh/tree/testing --debug
```

**Informazio gehiago aplikazioaren paketatzeari buruz:** <https://yunohost.org/packaging_apps>
