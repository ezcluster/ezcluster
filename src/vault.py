#
# Copyright (C) 2018 BROADSoftware
#
# This file is part of EzCluster
#
# EzCluster is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EzCluster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with EzCluster.  If not, see <http://www.gnu.org/licenses/lgpl-3.0.html>.

import ansible
from misc import ERROR, appendPath, file2String
import os
try:
    from ansible.parsing.vault import VaultLib
except ImportError:
    # Ansible<2.0
    from ansible.utils.vault import VaultLib

_ansible_ver = float('.'.join(ansible.__version__.split('.')[:2]))

VAULT_PASSWORD_FILES="vault_password_files"
VAULT_ID="vault_id"
FILE="file"
DATA="data"
CONFIG_FILE="configFile"

vaultFactory = None

def initVaultFactory(model):
    global vaultFactory
    vaultFactory = VaultFactory(model)

def getVault(vaultId):
    return vaultFactory.getVault(vaultId)

class VaultFactory(object):
    def __init__(self, model):
        self.model = model
        self.vaultById = {}
        
    def getVault(self, vaultId="default"):
        if vaultId in self.vaultById:
            return self.vaultById[vaultId]
        else:
            if VAULT_PASSWORD_FILES not in self.model["config"]:
                ERROR("{} is missing from configuration while encryption is used in some template".format(VAULT_PASSWORD_FILES))
            l = filter(lambda x: x["vault_id"] == vaultId, self.model["config"][VAULT_PASSWORD_FILES])
            if len(l) > 1:
                ERROR("{}: vault_id '{}' is defined twice in configuration file!".format(VAULT_PASSWORD_FILES, vaultId))
            if len(l) != 1:
                ERROR("{}: vault_id '{}' is not defined in configuration file!".format(VAULT_PASSWORD_FILES, vaultId))
            f = appendPath(os.path.dirname(self.model[DATA][CONFIG_FILE]), l[0][FILE])
            if not (os.path.isfile(f) and os.access(f, os.R_OK)):
                ERROR("Non existing or not accessible vault password file '{}'.".format(f))
            pwd = file2String(f)
            pwd = pwd.strip()
            vault = Vault(pwd)
            self.vaultById[vaultId] = vault
            return vault


class Vault(object):
    def __init__(self, password):
        self._ansible_ver = _ansible_ver

        self.secret = password.encode('utf-8')
        self.vault = VaultLib(self._make_secrets(self.secret))

    def _make_secrets(self, secret):
        if self._ansible_ver < 2.4:
            return secret

        from ansible.constants import DEFAULT_VAULT_ID_MATCH #@UnresolvedImport
        from ansible.parsing.vault import VaultSecret
        return [(DEFAULT_VAULT_ID_MATCH, VaultSecret(secret))]
    
    def encrypt(self, text):
        return self.vault.encrypt(text)

