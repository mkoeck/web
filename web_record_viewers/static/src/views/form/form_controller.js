/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillUnmount, useEffect, useState } from "@odoo/owl";

const PING_INTERVAL_MS = 30000;

patch(FormController.prototype, {
    setup() {
        this.viewerState = useState({ viewers: [] });
        this.busService = useService("bus_service");
        this._pingIntervalId = null;

        this._onBusUpdate = this._onBusUpdate.bind(this);

        this._subscribeToBus();
        this._getViewers();

        useEffect(
            () => {
                this._stopTracking();
                this._startTracking();
                this._getViewers();
            },
            () => [this.props.resModel, this.props.resId]
        );

        onWillUnmount(() => {
            this._stopTracking();
            this._unsubscribeFromBus();
        });

        super.setup();
    },

    // ----- Bus Management -----
    _subscribeToBus() {
        this.busService?.subscribe("record_viewers_update", this._onBusUpdate);
    },

    _unsubscribeFromBus() {
        this.busService?.unsubscribe("record_viewers_update", this._onBusUpdate);
    },

    // ----- Tracking Handlers -----
    _startTracking() {
        this._postViewers();
        this._startPingLoop();
    },

    _stopTracking() {
        this._clearPingLoop();
        this._deleteViewers();
    },

    _startPingLoop() {
        this._clearPingLoop();
        this._pingIntervalId = setInterval(() => this._postViewers(), PING_INTERVAL_MS);
    },

    _clearPingLoop() {
        if (this._pingIntervalId) {
            clearInterval(this._pingIntervalId);
            this._pingIntervalId = null;
        }
    },

    // ----- API Wrappers -----
    async _getViewers() {
        if (!this.props.resModel || !this.props.resId) return;
        try {
            const { data } = await this._apiRequest(`/record_viewers/${this.props.resModel}/${this.props.resId}`);
            this.viewerState.viewers = data;
        } catch (error) {
            console.warn("Failed to get viewers:", error);
        }
    },

    async _postViewers() {
        if (!this.props.resModel || !this.props.resId) return;
        try {
            await this._apiRequest(
                `/record_viewers/${this.props.resModel}/${this.props.resId}`,
                "POST",
                { csrf_token: odoo.csrf_token }
            );
        } catch (error) {
            console.warn("Failed to post viewers:", error);
        }
    },
    
    async _deleteViewers() {
        if (!this.props.resModel || !this.props.resId) return;
        try {
            await this._apiRequest(
                `/record_viewers/${this.props.resModel}/${this.props.resId}`,
                "DELETE",
                { csrf_token: odoo.csrf_token }
            );
        } catch (error) {
            console.warn("Failed to delete viewers:", error);
        }
    },

    async _apiRequest(endpoint, method = "GET", body = null) {
        const options = {
            method,
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        };
        if (body) {
            options.body = new URLSearchParams(body);
        }

        const response = await fetch(endpoint, options);
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    },

    // ----- Bus Callback -----
    _onBusUpdate({ res_model, res_id, viewers = [] } = {}) {
        if (this.props.resModel === res_model && this.props.resId === res_id) {
            this.viewerState.viewers = viewers;
        }
    },
});
