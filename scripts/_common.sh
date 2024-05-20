#!/bin/bash

#=================================================
# RETRIEVE ARGUMENTS FROM THE MANIFEST
#=================================================

# Transfer the main SSO domain to the App:
ynh_current_host=$(cat /etc/yunohost/current_host)
__YNH_CURRENT_HOST__=${ynh_current_host}

#=================================================
# ARGUMENTS FROM CONFIG PANEL
#=================================================

# 'debug_enabled' -> '__DEBUG_ENABLED__' -> settings.DEBUG
debug_enabled="0" # "1" or "0" string

# 'log_level' -> '__LOG_LEVEL__' -> settings.LOG_LEVEL
log_level="WARNING"

# 'admin_email' -> '__ADMIN_EMAIL__' add in settings.ADMINS
admin_email="${admin}@${domain}"

# 'default_from_email' -> '__DEFAULT_FROM_EMAIL__' -> settings.DEFAULT_FROM_EMAIL
default_from_email="${app}@${domain}"

#=================================================
# SET CONSTANTS
#=================================================

# e.g.: point pip cache to: /home/yunohost.app/$app/.cache/
XDG_CACHE_HOME="$data_dir/.cache/"

log_path=/var/log/$app
log_file="${log_path}/${app}.log"

#=================================================
# HELPERS
#=================================================

myynh_setup_python_venv() {
    # Always recreate everything fresh with current python version
    ynh_secure_remove "$data_dir/venv"

    chown -c -R "$app:" "$data_dir"

    # Skip pip because of: https://github.com/YunoHost/issues/issues/1960
    ynh_exec_as $app python3 -m venv --without-pip "$data_dir/venv"

    # run source in a 'sub shell'
    (
        set +o nounset
        source "$data_dir/venv/bin/activate"
        set -o nounset
        set -x
        cd "$data_dir"
        ynh_exec_as $app $data_dir/venv/bin/python3 -m ensurepip
        ynh_exec_as $app $data_dir/venv/bin/pip3 install --upgrade wheel pip setuptools
        ynh_exec_as $app $data_dir/venv/bin/pip3 install --no-deps -r "$data_dir/requirements.txt"
    )
}

myynh_setup_log_file() {
    (
        set -x

        mkdir -p "$(dirname "$log_file")"
        touch "$log_file"

        chown -c -R $app:$app "$log_path"
        chmod -c o-rwx "$log_path"
    )
}

myynh_fix_file_permissions() {
    (
        set -x

        # /var/www/$app/
        chown -c -R "$app:www-data" "$install_dir"
        chmod -c o-rwx "$install_dir"

        # /home/yunohost.app/$app/
        chown -c -R "$app:" "$data_dir"
        chmod -c o-rwx "$data_dir"
    )
}
