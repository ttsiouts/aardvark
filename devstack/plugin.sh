#!/bin/bash
# plugin.sh - devstack plugin for aardvark

# devstack plugin contract defined at:
# https://docs.openstack.org/devstack/latest/plugins.html

echo_summary "aardvark devstack plugin.sh called: $1/$2"
source $DEST/aardvark/devstack/src/aardvark

if is_service_enabled aardvark_reaper aardvark_notification; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "install" ]]; then
        # stack/install - Called after the layer 1 and 2 projects source and
        # their dependencies have been installed

            echo_summary "Installing Aardvark"
            install_aardvark

        elif [[ "$2" == "post-config" ]]; then
        # stack/post-config - Called after the layer 1 and 2 services have been
        # configured. All configuration files for enabled services should exist
        # at this point.

            echo_summary "Configuring Aardvark"
            configure_aardvark
            create_aardvark_accounts

        elif [[ "$2" == "extra" ]]; then
        # stack/extra - Called near the end after layer 1 and 2 services have
        # been started.

            echo_summary "Starting Aardvark"
            start_aardvark

        fi
    fi

    if [[ "$1" == "unstack" ]]; then
    # unstack - Called by unstack.sh before other services are shut down.

        stop_aardvark
    fi

    if [[ "$1" == "clean" ]]; then
    # clean - Called by clean.sh before other services are cleaned, but after
    # unstack.sh has been called.
        cleanup_aardvark
    fi
fi

