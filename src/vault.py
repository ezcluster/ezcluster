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
from ansible.parsing.vault import VaultLib
from ansible.parsing.vault import is_encrypted
import yaml
import logging

_ansible_ver = float('.'.join(ansible.__version__.split('.')[:2]))

VAULTS="vaults"

VAULT_PASSWORD_FILE="vaultPasswordFile"
VAULT_ID="vault_id"
PASSWORD_FILE="password_file"
DATA="data"
CONFIG_FILE="configFile"
CLUSTER="cluster"
SAFE_CONFIFG_FILE="safe_config_file"
SAFE_CONFIG="safeConfig"
_SAFE_CONFIG_FILE_="safeConfigFile"

logger = logging.getLogger("ezcluster.main")


vault = None

def getVault():
    if vault != None:
        return vault
    else:
        ERROR("'vault_id' is not defined while there is a need for encryption")

def initVault(model):
    global vault
    if VAULT_ID in model[CLUSTER]: 
        vaultId = model[CLUSTER][VAULT_ID]
        if VAULTS not in model["config"]:
            ERROR("{} is missing from configuration while encryption id required ('vault_id' is defined)".format(VAULTS))
        l = filter(lambda x: x["vault_id"] == vaultId, model["config"][VAULTS])
        if len(l) > 1:
            ERROR("{}: vault_id '{}' is defined twice in configuration file!".format(VAULTS, vaultId))
        if len(l) != 1:
            ERROR("{}: vault_id '{}' is not defined in configuration file!".format(VAULTS, vaultId))
        f = appendPath(os.path.dirname(model[DATA][CONFIG_FILE]), l[0][PASSWORD_FILE])
        if not (os.path.isfile(f) and os.access(f, os.R_OK)):
            ERROR("Non existing or not accessible vault password file '{}'.".format(f))
        pwd = file2String(f)
        pwd = pwd.strip()
        model[DATA][VAULT_PASSWORD_FILE] = f
        vault = Vault(pwd)
        if SAFE_CONFIFG_FILE in l[0]:
            scFileName = appendPath(os.path.dirname(model[DATA][CONFIG_FILE]), l[0][SAFE_CONFIFG_FILE])
            model[DATA][_SAFE_CONFIG_FILE_] = scFileName
            if not (os.path.isfile(scFileName) and os.access(scFileName, os.R_OK)):
                ERROR("Non existing or not accessible safe config file '{}'.".format(scFileName))
            logger.info("Loading safe config from '{}'".format(scFileName))
            data, was_encrypted = vault.encryptedFile2String(scFileName)
            safeConfig = yaml.load(data)
            model[SAFE_CONFIG] = safeConfig
            if not was_encrypted:
                print("\n'{}' was not encrypted. Will encrypt it".format(scFileName))
                vault.stringToEncryptedFile(data, scFileName)
    else:
        vault = None
    
class Vault(object):
    def __init__(self, password):
        self._ansible_ver = _ansible_ver

        self.secret = password.encode('utf-8')
        self.vaultLib = VaultLib(self._make_secrets(self.secret))

    def _make_secrets(self, secret):
        if self._ansible_ver < 2.4:
            return secret

        from ansible.constants import DEFAULT_VAULT_ID_MATCH #@UnresolvedImport
        from ansible.parsing.vault import VaultSecret
        return [(DEFAULT_VAULT_ID_MATCH, VaultSecret(secret))]
    
    def encrypt(self, text):
        return self.vaultLib.encrypt(text)

    def encryptedFile2String(self, fileName):
        data = file2String(fileName)
        was_encrypted = False
        if is_encrypted(data):
            was_encrypted = True
            data = self.vaultLib.decrypt(data)
        return data, was_encrypted
            
    def stringToEncryptedFile(self, data, filename):
        data = self.encrypt(data)
        stream = file(filename, 'w')
        stream.write(data)
        stream.close()

        