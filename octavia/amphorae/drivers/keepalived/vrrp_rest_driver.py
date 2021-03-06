# Copyright 2015 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging

from octavia.amphorae.drivers import driver_base
from octavia.amphorae.drivers.keepalived.jinja import jinja_cfg
from octavia.common import constants

LOG = logging.getLogger(__name__)
API_VERSION = constants.API_VERSION


class KeepalivedAmphoraDriverMixin(driver_base.VRRPDriverMixin):
    def __init__(self):
        super(KeepalivedAmphoraDriverMixin, self).__init__()

        # The Mixed class must define a self.client object for the
        # AmphoraApiClient

    def update_vrrp_conf(self, loadbalancer, amphorae_network_config):
        """Update amphorae of the loadbalancer with a new VRRP configuration

        :param loadbalancer: loadbalancer object
        :param amphorae_network_config: amphorae network configurations
        """
        templater = jinja_cfg.KeepalivedJinjaTemplater()

        LOG.debug("Update loadbalancer %s amphora VRRP configuration.",
                  loadbalancer.id)

        for amp in filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):

            self._populate_amphora_api_version(amp)
            # Get the VIP subnet prefix for the amphora
            # For amphorav2 amphorae_network_config will be list of dicts
            try:
                vip_cidr = amphorae_network_config[amp.id].vip_subnet.cidr
            except AttributeError:
                vip_cidr = amphorae_network_config[amp.id][
                    constants.VIP_SUBNET][constants.CIDR]

            # Generate Keepalived configuration from loadbalancer object
            config = templater.build_keepalived_config(
                loadbalancer, amp, vip_cidr)
            self.clients[amp.api_version].upload_vrrp_config(amp, config)

    def stop_vrrp_service(self, loadbalancer):
        """Stop the vrrp services running on the loadbalancer's amphorae

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Stop loadbalancer %s amphora VRRP Service.",
                 loadbalancer.id)

        for amp in filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):

            self._populate_amphora_api_version(amp)
            self.clients[amp.api_version].stop_vrrp(amp)

    def start_vrrp_service(self, loadbalancer):
        """Start the VRRP services of all amphorae of the loadbalancer

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Start loadbalancer %s amphora VRRP Service.",
                 loadbalancer.id)

        for amp in filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):

            LOG.debug("Start VRRP Service on amphora %s .", amp.lb_network_ip)
            self._populate_amphora_api_version(amp)
            self.clients[amp.api_version].start_vrrp(amp)

    def reload_vrrp_service(self, loadbalancer):
        """Reload the VRRP services of all amphorae of the loadbalancer

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Reload loadbalancer %s amphora VRRP Service.",
                 loadbalancer.id)

        for amp in filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):

            self._populate_amphora_api_version(amp)
            self.clients[amp.api_version].reload_vrrp(amp)

    def get_vrrp_interface(self, amphora, timeout_dict=None):
        self._populate_amphora_api_version(amphora)
        return self.clients[amphora.api_version].get_interface(
            amphora, amphora.vrrp_ip, timeout_dict=timeout_dict)['interface']
