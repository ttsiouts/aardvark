from keystoneauth1 import loading as ks_loading
from oslo_config import cfg


SERVICE_TYPE = 'placement'

placement_group = cfg.OptGroup(
    'placement',
    title='Placement Service Options',
    help="Configuration options for connecting to the placement API service")

placement_opts = [
    # Add conf options for Placement
]


def register_opts(conf):

    conf.register_group(placement_group)
    conf.register_opts(placement_opts, group=placement_group)

    group = getattr(placement_group, 'name', placement_group)

    ks_loading.register_session_conf_options(conf, group)
    ks_loading.register_auth_conf_options(conf, group)

    adapter_opts = get_ksa_adapter_opts(SERVICE_TYPE)
    conf.register_opts(adapter_opts, group=group)

def get_ksa_adapter_opts(default_service_type, deprecated_opts=None):

    opts = ks_loading.get_adapter_conf_options(
        include_deprecated=False, deprecated_opts=deprecated_opts)

    cfg.set_defaults(opts,
                     valid_interfaces=['internal', 'public'],
                     service_type=default_service_type)
    return opts
