# -*- coding: utf-8 -*-
# Copyright (c) 2015 Spotify AB

from __future__ import absolute_import, division, print_function

import re

from six import iterkeys

from .errors import *  # NOQA


#####
# RAMLRoot validators
#####

def root_version(inst, attr, value):
    """Require an API Version (e.g. api.foo.com/v1)."""
    base_uri = inst.raml_obj.get("baseUri")
    if not value and"{version}" in base_uri:
        msg = ("RAML File's baseUri includes {version} parameter but no "
               "version is defined.")
        inst.errors.append(InvalidRootNodeError(msg))
        return
    elif not value:
        msg = "RAML File does not define an API version."
        inst.errors.append(InvalidRootNodeError(msg))
        return


def root_base_uri(inst, attr, value):
    """Require a Base URI."""
    if not value:
        msg = "RAML File does not define the baseUri."
        inst.errors.append(InvalidRootNodeError(msg))
        return


def root_base_uri_params(inst, attr, value):
    """
    Require that Base URI parameters have a ``default`` parameter set.
    """
    if value:
        for v in value:
            if not v.default:
                msg = ("The 'default' parameter is not set for base URI "
                       "parameter '{0}'".format(v.name))
                inst.errors.append(InvalidRootNodeError(msg))
                return


def root_uri_params(inst, attr, value):
    """
    Assert that where is no ``version`` parameter in the regular URI parameters
    """
    if value:
        for v in value:
            if v.name == "version":
                msg = "'version' can only be defined in baseUriParameters."
                inst.errors.append(InvalidRootNodeError(msg))
                return


def root_protocols(inst, attr, value):
    """
    Only support HTTP/S plus what is defined in user-config
    """
    if value:
        for p in value:
            if p.upper() not in inst.config.get("protocols"):
                msg = ("'{0}' not a valid protocol for a RAML-defined "
                       "API.".format(p))
                inst.errors.append(InvalidRootNodeError(msg))
                return


def root_title(inst, attr, value):
    """
    Require a title for the defined API.
    """
    if not value:
        msg = "RAML File does not define an API title."
        inst.errors.append(InvalidRootNodeError(msg))
        return


def root_docs(inst, attr, value):
    """
    Assert that if there is ``documentation`` defined in the root of the
    RAML file, that it contains a ``title`` and ``content``.
    """
    if value:
        for d in value:
            if d.title.raw is None:
                msg = "API Documentation requires a title."
                inst.errors.append(InvalidRootNodeError(msg))
                return
            if d.content.raw is None:
                msg = "API Documentation requires content defined."
                inst.errors.append(InvalidRootNodeError(msg))
                return


# TODO: finish
def root_schemas(inst, attr, value):
    pass


def root_media_type(inst, attr, value):
    """
    Only support media types based on config and regex
    """
    if value:
        match = validate_mime_type(value)
        if value not in inst.config.get("media_types") and not match:
            msg = "Unsupported MIME Media Type: '{0}'.".format(value)
            inst.errors.append(InvalidRootNodeError(msg))
            return


def root_resources(inst, attr, value):
    if not value:
        msg = "API does not define any resources."
        inst.errors.append(InvalidRootNodeError(msg))
        return


def root_secured_by(inst, attr, value):
    pass


#####
# Shared Validators for Resource & Resource Type Node
#####
def assigned_traits(inst, attr, value):
    """
    Assert assigned traits are defined in the RAML Root and correctly
    represented in the RAML.
    """
    if value:
        traits = inst.root.raw.get("traits", {})
        if not traits:
            msg = ("Trying to assign traits that are not defined"
                   "in the root of the API.")
            inst.errors.append(InvalidResourceNodeError(msg))
            return
        trait_names = [list(iterkeys(i))[0] for i in traits]
        if isinstance(value, list):
            for v in value:
                if isinstance(v, dict):
                    if list(iterkeys(v))[0] not in trait_names:  # NOCOV
                        msg = (
                            "Trait '{0}' is assigned to '{1}' but is not def"
                            "ined in the root of the API.".format(v, inst.path)
                        )
                        inst.errors.append(InvalidResourceNodeError(msg))
                        return
                    if not isinstance(v.keys()[0], str):  # NOCOV
                        msg = ("'{0}' needs to be a string referring to a "
                               "trait, or a dictionary mapping parameter "
                               "values to a trait".format(v))
                        inst.errors.append(InvalidResourceNodeError(msg))
                        return
                elif isinstance(v, str):
                    if v not in trait_names:
                        msg = (
                            "Trait '{0}' is assigned to '{1}' but is not "
                            "defined in the root of the API.".format(v,
                                                                     inst.path)
                        )
                        inst.errors.append(InvalidResourceNodeError(msg))
                        return
                else:
                    msg = ("'{0}' needs to be a string referring to a "
                           "trait, or a dictionary mapping parameter "
                           "values to a trait".format(v))
                    inst.errors.append(InvalidResourceNodeError(msg))
                    return


def assigned_res_type(inst, attr, value):
    """
    Assert only one (or none) assigned resource type is defined in the RAML
    Root and correctly represented in the RAML.
    """
    if value:
        if isinstance(value, tuple([dict, list])) and len(value) > 1:
            msg = "Too many resource types applied to '{0}'.".format(
                inst.display_name
            )
            inst.errors.append(InvalidResourceNodeError(msg))
            return

        res_types = inst.root.raw.get("resourceTypes", {})
        res_type_names = [list(iterkeys(i))[0] for i in res_types]
        if isinstance(value, list):
            item = value[0]  # NOCOV
        elif isinstance(value, dict):
            item = list(iterkeys(value))[0]  # NOCOV
        else:
            item = value
        if item not in res_type_names:
            msg = ("Resource Type '{0}' is assigned to '{1}' but is not "
                   "defined in the root of the API.".format(value,
                                                            inst.display_name))
            inst.errors.append(InvalidResourceNodeError(msg))
            return


#####
# Parameter Validators
#####
def header_type(inst, attr, value):
    """Supported header type"""
    if value and value not in inst.config.get("prim_types"):
        msg = "'{0}' is not a valid primative parameter type".format(value)
        inst.errors.append(InvalidParameterError(msg, "header"))
        return


def body_mime_type(inst, attr, value):
    """Supported MIME media type for request/response"""
    if value:
        match = validate_mime_type(value)
        if value not in inst.config.get("media_types") and not match:
            msg = "Unsupported MIME Media Type: '{0}'.".format(value)
            inst.errors.append(InvalidParameterError(msg, "body"))
            return


def body_schema(inst, attr, value):
    """
    Assert no ``schema`` is defined if body as a form-related MIME media type
    """
    form_types = ["multipart/form-data", "application/x-www-form-urlencoded"]
    if inst.mime_type in form_types and value:
        msg = "Body must define formParameters, not schema/example."
        inst.errors.append(InvalidParameterError(msg, "body"))
        return


def body_example(inst, attr, value):
    """
    Assert no ``example`` is defined if body as a form-related MIME media type
    """
    form_types = ["multipart/form-data", "application/x-www-form-urlencoded"]
    if inst.mime_type in form_types and value:
        msg = "Body must define formParameters, not schema/example."
        inst.errors.append(InvalidParameterError(msg, "body"))
        return


def body_form(inst, attr, value):
    """
    Assert ``formParameters`` are defined if body has a form-related
    MIME type.
    """
    form_types = ["multipart/form-data", "application/x-www-form-urlencoded"]
    if inst.mime_type in form_types and not value:
        msg = "Body with mime_type '{0}' requires formParameters.".format(
            inst.mime_type)
        inst.errors.append(InvalidParameterError(msg, "body"))
        return


def response_code(inst, attr, value):
    """
    Assert a valid response code.
    """
    if not isinstance(value, int):
        msg = ("Response code '{0}' must be an integer representing an "
               "HTTP code.".format(value))
        inst.errors.append(InvalidParameterError(msg, "response"))
        return
    if value not in inst.config.get("resp_codes"):
        msg = "'{0}' not a valid HTTP response code.".format(value)
        inst.errors.append(InvalidParameterError(msg, "response"))
        return


#####
# Primative Validators
#####
def integer_number_type_parameter(inst, attr, value):
    """
    Assert correct parameter attributes for ``integer`` or ``number``
    primative parameter types.
    """
    if value is not None:
        param_types = ["integer", "number"]
        if inst.type not in param_types:
            msg = ("{0} must be either a number or integer to have {1} "
                   "attribute set, not '{2}'.".format(inst.name, attr.name,
                                                      inst.type))
            inst.errors.append(InvalidParameterError(msg, "BaseParameter"))
            return


def string_type_parameter(inst, attr, value):
    """
    Assert correct parameter attributes for ``string`` primative parameter
    types.
    """
    if value:
        if inst.type != "string":
            msg = ("{0} must be a string type to have {1} "
                   "attribute set, not '{2}'.".format(inst.name, attr.name,
                                                      inst.type))
            inst.errors.append(InvalidParameterError(msg, "BaseParameter"))
            return


#####
# Util/common functions
#####


def validate_mime_type(value):
    """
    Assert a valid MIME media type for request/response body.
    """
    regex_str = re.compile(r"application\/[A-Za-z.-0-1]*?(json|xml)")
    match = re.search(regex_str, value)
    return match
