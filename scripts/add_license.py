# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>

import os

from pathlib import Path

# GPL-3.0 License header
license_header = '''\
# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>
'''

def add_license_header(file_path) -> bool:
    with open(file_path, 'r+') as f:
        content = f.read()

        if license_header in content:
            return False

        f.seek(0, 0)
        f.write(license_header.lstrip('\n') + '\n' + content)
        return True


for file in Path(".").rglob("*.py"):
    add_license_header(file)
    print(f"-> Added license header to {file}")