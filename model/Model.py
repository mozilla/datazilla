#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
import datetime
import time
import os

if "APPENGINE_RUNTIME" in os.environ:
    from datazilla.model.appengine.model import Model as Model
else:
    from datazilla.model.sql.model import Model as Model
