// Simple reactive state store with event subscriptions

class State {
    constructor() {
        this._data = {};
        this._listeners = {};
    }

    get(key) {
        return this._data[key];
    }

    set(key, value) {
        this._data[key] = value;
        const listeners = this._listeners[key];
        if (listeners) {
            for (const fn of listeners) {
                fn(value);
            }
        }
    }

    on(key, callback) {
        if (!this._listeners[key]) {
            this._listeners[key] = [];
        }
        this._listeners[key].push(callback);
        // Return unsubscribe function
        return () => {
            this._listeners[key] = this._listeners[key].filter(fn => fn !== callback);
        };
    }

    keys() {
        return Object.keys(this._data);
    }
}

export const state = new State();
