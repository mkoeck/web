from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
from functools import wraps

def with_model_access(method):
    """
    Decorator to validate that the current user has read access to the
    given model record before executing the controller method.

    It uses `check_access('read')`, which internally calls both:
    - check_access_rights(): verifies the user has read permission at the model level (ACL)
    - check_access_rule(): checks record-level domain rules (e.g., `['user_id', '=', user.id]`)

    If access is denied, a 403 response is returned to the client.

    This ensures the user is only allowed to interact with viewer data
    for records they could legitimately open in the UI.
    """
    @wraps(method)
    def wrapper(self, res_model, res_id, **kwargs):
        try:
            request.env[res_model].browse(res_id).check_access('read') # type: ignore
        except AccessError:
            return request.make_json_response({'status': 'forbidden'}, status=403)
        return method(self, res_model, res_id, **kwargs)
    return wrapper


class RecordViewersController(http.Controller):
    """
    HTTP controller exposing record viewer endpoints.
    All routes are protected with access checks to ensure that the
    current user may only interact with viewer data for records
    they have legitimate access to.

    The core operations (start/stop/view) are delegated to the `record.viewer`
    model, using `sudo()` to bypass its ACLs — this is safe because access
    to the underlying record is verified beforehand by the decorator.
    """

    def _get_model_id(self, res_model):
        """
        Resolves the internal ir.model ID for a given model name.
        """
        return request.env['ir.model']._get_id(res_model)

    def _respond_ok(self, data=None):
        """
        Returns a JSON response with status 'ok' and optional payload data.
        """
        return request.make_json_response({'status': 'ok', 'data': data} if data is not None else {'status': 'ok'})

    @http.route('/record_viewers/<string:res_model>/<int:res_id>', type='http', auth='user', methods=['POST'])
    @with_model_access
    def post_record_viewers(self, res_model, res_id, **kwargs):
        """
        Registers or updates the viewer session for the current user.

        Uses sudo to bypass access rules on the `record.viewer` model itself.
        This is safe because access to the target record has already been validated
        by the `@with_model_access` decorator.
        """
        res_model_id = self._get_model_id(res_model)
        request.env['record.viewer'].sudo()._start_session(res_model_id, res_id)
        return self._respond_ok()

    @http.route('/record_viewers/<string:res_model>/<int:res_id>', type='http', auth='user', methods=['DELETE'])
    @with_model_access
    def delete_record_viewers(self, res_model, res_id, **kwargs):
        """
        Ends the viewer session for the current user.

        Uses sudo to allow the deletion without being blocked by record rules
        on the `record.viewer` model. This is safe because we already confirmed
        the user can access the target record.
        """
        res_model_id = self._get_model_id(res_model)
        request.env['record.viewer'].sudo()._stop_session(res_model_id, res_id)
        return self._respond_ok()

    @http.route('/record_viewers/<string:res_model>/<int:res_id>', type='http', auth='user', methods=['GET'])
    @with_model_access
    def get_record_viewers(self, res_model, res_id, **kwargs):
        """
        Retrieves a list of currently active viewers for the given record.

        The result includes only recent sessions, filtered by timestamp.
        Uses sudo to bypass restrictions on the `record.viewer` model
        because the underlying record’s access has been enforced already.
        """
        res_model_id = self._get_model_id(res_model)
        data = request.env['record.viewer'].sudo()._get_viewers(res_model_id, res_id)
        return self._respond_ok(data=data)
