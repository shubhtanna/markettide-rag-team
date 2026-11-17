/**
 * MarketTideBus - Bi-Directional High-Performance Client Event Bus
 * 
 * Supports local Pub/Sub within the page and cross-frame bridging via window.postMessage.
 * Seamlessly connects the Three.js 3D Stock Nebula, Executive Workstation Shell, and RAG Chatbot.
 * 
 * Standard Event Schemas:
 * - 'market-tide:node-select' (Click-to-RAG)
 * - 'market-tide:scene-action' (Chatbot-to-3D)
 */
(function(global) {
  'use strict';

  class MarketTideEventBus {
    constructor() {
      this._handlers = new Map();
      this._initBridge();
    }

    /**
     * Subscribe to an event topic.
     * @param {string} event - Event name
     * @param {Function} handler - Callback receiving event payload
     * @returns {Function} Unsubscribe function
     */
    on(event, handler) {
      if (typeof handler !== 'function') {
        throw new TypeError('[MarketTideBus] Handler must be a function');
      }
      if (!this._handlers.has(event)) {
        this._handlers.set(event, new Set());
      }
      this._handlers.get(event).add(handler);
      return () => this.off(event, handler);
    }

    /**
     * Unsubscribe from an event topic.
     * @param {string} event - Event name
     * @param {Function} handler - Callback to remove
     */
    off(event, handler) {
      if (this._handlers.has(event)) {
        this._handlers.get(event).delete(handler);
        if (this._handlers.get(event).size === 0) {
          this._handlers.delete(event);
        }
      }
    }

    /**
     * Emit an event locally and optionally broadcast across window/iframe boundaries.
     * @param {string} event - Event name
     * @param {Object} payload - Event payload object
     * @param {boolean} [broadcast=true] - Whether to relay across frame boundaries
     */
    emit(event, payload = {}, broadcast = true) {
      // 1. In-process subscribers
      if (this._handlers.has(event)) {
        const callbacks = Array.from(this._handlers.get(event));
        for (let i = 0; i < callbacks.length; i++) {
          try {
            callbacks[i](payload);
          } catch (err) {
            console.error(`[MarketTideBus] Error executing subscriber for '${event}':`, err);
          }
        }
      }

      // 2. Dispatch DOM CustomEvent if in browser environment
      if (typeof global.dispatchEvent === 'function' && typeof CustomEvent !== 'undefined') {
        try {
          global.dispatchEvent(new CustomEvent(event, { detail: payload }));
        } catch (e) {
          // Ignore DOM dispatch failure in non-browser environments
        }
      }

      // 3. Cross-Frame postMessage broadcast
      if (broadcast && typeof global.postMessage === 'function') {
        const messagePacket = {
          _source: 'MarketTideBus',
          event: event,
          payload: payload,
          timestamp: payload && payload.timestamp ? payload.timestamp : Date.now()
        };

        // Broadcast to parent window if inside an iframe
        try {
          if (global.parent && global.parent !== global) {
            global.parent.postMessage(messagePacket, '*');
          }
        } catch (e) {
          // Cross-origin access restriction fallback
        }

        // Broadcast to child iframes if document is accessible
        if (typeof document !== 'undefined' && typeof document.querySelectorAll === 'function') {
          try {
            const iframes = document.querySelectorAll('iframe');
            for (let j = 0; j < iframes.length; j++) {
              const iframe = iframes[j];
              if (iframe.contentWindow) {
                iframe.contentWindow.postMessage(messagePacket, '*');
              }
            }
          } catch (e) {
            // Frame traversal warning
          }
        }
      }
    }

    /**
     * Helper to create and emit a Click-to-RAG node selection event.
     */
    emitNodeSelect(stockData) {
      const payload = {
        ticker: stockData.ticker || '',
        company: stockData.company || stockData.name || '',
        sector: stockData.sector || '',
        conglomerateGroup: stockData.conglomerateGroup || stockData.group || '',
        importanceScore: stockData.importanceScore || stockData.importance || 0,
        livePrice: stockData.livePrice || stockData.price || 0,
        percentageChange: stockData.percentageChange !== undefined ? stockData.percentageChange : (stockData.change || 0),
        sparkline: Array.isArray(stockData.sparkline) ? stockData.sparkline.slice(-30) : [],
        actionPrompt: stockData.actionPrompt || `Summarize recent corporate disclosures and filing impact for ${stockData.ticker || ''} (${stockData.company || stockData.name || ''})`,
        timestamp: Date.now()
      };
      this.emit('market-tide:node-select', payload);
      return payload;
    }

    /**
     * Helper to create and emit a Chatbot-to-3D scene action directive event.
     */
    emitSceneAction(directive) {
      const payload = {
        action: directive.action || 'HIGHLIGHT_TICKERS', // 'CLUSTER_CONGLOMERATE' | 'FOCUS_NODE' | 'HIGHLIGHT_TICKERS' | 'RESET_VIEW'
        conglomerate_group: directive.conglomerate_group || directive.group || '',
        ticker: directive.ticker || '',
        target_tickers: Array.isArray(directive.target_tickers) ? directive.target_tickers : (directive.tickers || []),
        visual_directives: Object.assign({
          camera_mode: 'FOCUS_CLUSTER_CENTROID',
          camera_transition_ms: 1100,
          glow_color: '#f97316',
          dim_unmatched_opacity: 0.15,
          render_connecting_rays: true,
          ray_color: '#f97316'
        }, directive.visual_directives || {}),
        timestamp: Date.now()
      };
      this.emit('market-tide:scene-action', payload);
      return payload;
    }

    /**
     * Initialize cross-window message listener.
     */
    _initBridge() {
      if (typeof global.addEventListener === 'function') {
        global.addEventListener('message', (event) => {
          if (!event.data || typeof event.data !== 'object') return;
          if (event.data._source !== 'MarketTideBus') return;

          const topic = event.data.event;
          const payload = event.data.payload;

          if (topic && payload) {
            // Re-emit locally without re-broadcasting over postMessage
            this.emit(topic, payload, false);
          }
        });
      }
    }
  }

  const busInstance = new MarketTideEventBus();

  // Export for browser global
  if (typeof window !== 'undefined') {
    window.MarketTideBus = busInstance;
  }
  // Export for CommonJS / Node.js verification tests
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      MarketTideEventBus,
      MarketTideBus: busInstance
    };
  }
  // Export for globalThis (Workers / other contexts)
  if (typeof globalThis !== 'undefined') {
    globalThis.MarketTideBus = busInstance;
  }

})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
