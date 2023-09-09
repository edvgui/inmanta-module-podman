"""
    Copyright 2023 Guillaume Everarts de Velp

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Contact: edvgui@gmail.com
"""
import inmanta.plugins


@inmanta.plugins.plugin()
def inline_options(options: "dict") -> "string":  # type: ignore
    """
    Convert a dict of options into a comma-separated list of key=value pairs.

    :param options: The options dict to serialize into a string.
    """
    return ",".join(f"{k}={v}" for k, v in options.items() if v is not None)


@inmanta.plugins.plugin()
def join(parts: "string[]", *, separator: "string") -> "string":  # type: ignore
    """
    Join all the elements in the list together, use the separator in
    between each joined part.

    :param parts: The list of string we want to join
    :param separator: The separator to use in the join
    """
    return separator.join(parts)
