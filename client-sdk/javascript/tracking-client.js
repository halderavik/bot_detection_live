/**
 * Bot Detection JavaScript Tracking Client
 * 
 * This client collects user behavior events and sends them to the Bot Detection API
 * for analysis. It tracks keystrokes, mouse movements, scroll events, and focus changes.
 */

(function(window) {
    'use strict';

    // Configuration
    const DEFAULT_CONFIG = {
        apiBaseUrl: 'http://localhost:8000/api/v1',
        sessionId: null,
        batchSize: 10,
        flushInterval: 5000, // 5 seconds
        debug: false,
        enabled: true,
        trackKeystrokes: true,
        trackMouse: true,
        trackScroll: true,
        trackFocus: true,
        trackPageLoad: true
    };

    class BotDetectionTracker {
        constructor(config = {}) {
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.events = [];
            this.sessionId = this.config.sessionId;
            this.isInitialized = false;
            this.flushTimer = null;
            this.lastMouseMove = { x: 0, y: 0 };
            this.lastScroll = { x: 0, y: 0 };
            this.pageLoadStart = performance.now();
            
            this.log('Bot Detection Tracker initialized', this.config);
        }

        /**
         * Initialize the tracker and start collecting events
         */
        async init() {
            if (this.isInitialized) {
                this.log('Tracker already initialized');
                return;
            }

            if (!this.config.enabled) {
                this.log('Tracker is disabled');
                return;
            }

            try {
                // Create session if not provided
                if (!this.sessionId) {
                    this.sessionId = await this.createSession();
                }

                // Setup event listeners
                this.setupEventListeners();
                
                // Start periodic flushing
                this.startFlushTimer();
                
                this.isInitialized = true;
                this.log('Tracker initialized successfully', { sessionId: this.sessionId });
                
            } catch (error) {
                this.log('Failed to initialize tracker', error);
                throw error;
            }
        }

        /**
         * Create a new session
         */
        async createSession() {
            try {
                const response = await fetch(`${this.config.apiBaseUrl}/detection/sessions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_agent: navigator.userAgent,
                        page_url: window.location.href,
                        page_title: document.title
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                return data.session_id;
            } catch (error) {
                this.log('Failed to create session', error);
                throw error;
            }
        }

        /**
         * Setup event listeners for user behavior tracking
         */
        setupEventListeners() {
            // Keystroke tracking
            if (this.config.trackKeystrokes) {
                document.addEventListener('keydown', this.handleKeyDown.bind(this));
            }

            // Mouse tracking
            if (this.config.trackMouse) {
                document.addEventListener('click', this.handleMouseClick.bind(this));
                document.addEventListener('mousemove', this.handleMouseMove.bind(this));
            }

            // Scroll tracking
            if (this.config.trackScroll) {
                window.addEventListener('scroll', this.handleScroll.bind(this));
            }

            // Focus tracking
            if (this.config.trackFocus) {
                document.addEventListener('focusin', this.handleFocusIn.bind(this));
                document.addEventListener('focusout', this.handleFocusOut.bind(this));
            }

            // Page load tracking
            if (this.config.trackPageLoad) {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', this.handlePageLoad.bind(this));
                } else {
                    this.handlePageLoad();
                }
            }

            // Page unload - flush events
            window.addEventListener('beforeunload', this.flush.bind(this));
        }

        /**
         * Handle keydown events
         */
        handleKeyDown(event) {
            const target = event.target;
            const eventData = {
                event_type: 'keystroke',
                timestamp: new Date().toISOString(),
                key: event.key,
                key_code: event.keyCode,
                element_id: target.id || null,
                element_type: target.tagName.toLowerCase(),
                element_class: target.className || null,
                page_url: window.location.href,
                page_title: document.title,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                event_data: {
                    key: event.key,
                    key_code: event.keyCode,
                    ctrl_key: event.ctrlKey,
                    alt_key: event.altKey,
                    shift_key: event.shiftKey,
                    meta_key: event.metaKey
                }
            };

            this.addEvent(eventData);
        }

        /**
         * Handle mouse click events
         */
        handleMouseClick(event) {
            const target = event.target;
            const eventData = {
                event_type: 'mouse_click',
                timestamp: new Date().toISOString(),
                x: event.clientX,
                y: event.clientY,
                button: event.button,
                element_id: target.id || null,
                element_type: target.tagName.toLowerCase(),
                element_class: target.className || null,
                page_url: window.location.href,
                page_title: document.title,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                event_data: {
                    x: event.clientX,
                    y: event.clientY,
                    button: event.button,
                    ctrl_key: event.ctrlKey,
                    alt_key: event.altKey,
                    shift_key: event.shiftKey,
                    meta_key: event.metaKey
                }
            };

            this.addEvent(eventData);
        }

        /**
         * Handle mouse move events (throttled)
         */
        handleMouseMove(event) {
            // Throttle mouse move events to avoid overwhelming the API
            const now = Date.now();
            const distance = Math.sqrt(
                Math.pow(event.clientX - this.lastMouseMove.x, 2) +
                Math.pow(event.clientY - this.lastMouseMove.y, 2)
            );

            // Only track if mouse moved significantly or enough time has passed
            if (distance > 10 || now - this.lastMouseMove.timestamp > 1000) {
                const target = event.target;
                const eventData = {
                    event_type: 'mouse_move',
                    timestamp: new Date().toISOString(),
                    x: event.clientX,
                    y: event.clientY,
                    element_id: target.id || null,
                    element_type: target.tagName.toLowerCase(),
                    element_class: target.className || null,
                    page_url: window.location.href,
                    page_title: document.title,
                    screen_width: window.screen.width,
                    screen_height: window.screen.height,
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight,
                    event_data: {
                        x: event.clientX,
                        y: event.clientY,
                        movement_x: event.movementX,
                        movement_y: event.movementY
                    }
                };

                this.addEvent(eventData);
                
                this.lastMouseMove = {
                    x: event.clientX,
                    y: event.clientY,
                    timestamp: now
                };
            }
        }

        /**
         * Handle scroll events (throttled)
         */
        handleScroll(event) {
            const now = Date.now();
            const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollY = window.pageYOffset || document.documentElement.scrollTop;

            // Only track if scroll position changed significantly
            if (Math.abs(scrollX - this.lastScroll.x) > 5 || 
                Math.abs(scrollY - this.lastScroll.y) > 5) {
                
                const eventData = {
                    event_type: 'scroll',
                    timestamp: new Date().toISOString(),
                    scroll_x: scrollX,
                    scroll_y: scrollY,
                    page_url: window.location.href,
                    page_title: document.title,
                    screen_width: window.screen.width,
                    screen_height: window.screen.height,
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight,
                    event_data: {
                        scroll_x: scrollX,
                        scroll_y: scrollY,
                        scroll_width: document.documentElement.scrollWidth,
                        scroll_height: document.documentElement.scrollHeight
                    }
                };

                this.addEvent(eventData);
                
                this.lastScroll = { x: scrollX, y: scrollY };
            }
        }

        /**
         * Handle focus in events
         */
        handleFocusIn(event) {
            const target = event.target;
            const eventData = {
                event_type: 'focus',
                timestamp: new Date().toISOString(),
                element_id: target.id || null,
                element_type: target.tagName.toLowerCase(),
                element_class: target.className || null,
                page_url: window.location.href,
                page_title: document.title,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                event_data: {
                    element_id: target.id,
                    element_type: target.tagName.toLowerCase(),
                    element_class: target.className
                }
            };

            this.addEvent(eventData);
        }

        /**
         * Handle focus out events
         */
        handleFocusOut(event) {
            const target = event.target;
            const eventData = {
                event_type: 'blur',
                timestamp: new Date().toISOString(),
                element_id: target.id || null,
                element_type: target.tagName.toLowerCase(),
                element_class: target.className || null,
                page_url: window.location.href,
                page_title: document.title,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                event_data: {
                    element_id: target.id,
                    element_type: target.tagName.toLowerCase(),
                    element_class: target.className
                }
            };

            this.addEvent(eventData);
        }

        /**
         * Handle page load event
         */
        handlePageLoad() {
            const loadTime = performance.now() - this.pageLoadStart;
            const eventData = {
                event_type: 'page_load',
                timestamp: new Date().toISOString(),
                page_url: window.location.href,
                page_title: document.title,
                load_time: loadTime,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                event_data: {
                    page_url: window.location.href,
                    page_title: document.title,
                    load_time: loadTime,
                    referrer: document.referrer
                }
            };

            this.addEvent(eventData);
        }

        /**
         * Add an event to the queue
         */
        addEvent(eventData) {
            this.events.push(eventData);
            
            // Flush if batch size reached
            if (this.events.length >= this.config.batchSize) {
                this.flush();
            }
        }

        /**
         * Start the periodic flush timer
         */
        startFlushTimer() {
            if (this.flushTimer) {
                clearInterval(this.flushTimer);
            }
            
            this.flushTimer = setInterval(() => {
                this.flush();
            }, this.config.flushInterval);
        }

        /**
         * Flush events to the API
         */
        async flush() {
            if (this.events.length === 0 || !this.sessionId) {
                return;
            }

            const eventsToSend = [...this.events];
            this.events = [];

            try {
                const response = await fetch(`${this.config.apiBaseUrl}/detection/sessions/${this.sessionId}/events`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(eventsToSend)
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                this.log(`Sent ${result.events_processed} events`);
                
            } catch (error) {
                this.log('Failed to send events', error);
                // Re-add events to queue for retry
                this.events.unshift(...eventsToSend);
            }
        }

        /**
         * Analyze the current session
         */
        async analyze() {
            if (!this.sessionId) {
                throw new Error('No active session');
            }

            try {
                // Flush any pending events first
                await this.flush();

                const response = await fetch(`${this.config.apiBaseUrl}/detection/sessions/${this.sessionId}/analyze`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                this.log('Analysis completed', result);
                return result;
                
            } catch (error) {
                this.log('Failed to analyze session', error);
                throw error;
            }
        }

        /**
         * Get session status
         */
        async getStatus() {
            if (!this.sessionId) {
                throw new Error('No active session');
            }

            try {
                const response = await fetch(`${this.config.apiBaseUrl}/detection/sessions/${this.sessionId}/status`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();
                
            } catch (error) {
                this.log('Failed to get session status', error);
                throw error;
            }
        }

        /**
         * Destroy the tracker and cleanup
         */
        destroy() {
            this.isInitialized = false;
            
            if (this.flushTimer) {
                clearInterval(this.flushTimer);
                this.flushTimer = null;
            }
            
            // Remove event listeners
            document.removeEventListener('keydown', this.handleKeyDown);
            document.removeEventListener('click', this.handleMouseClick);
            document.removeEventListener('mousemove', this.handleMouseMove);
            window.removeEventListener('scroll', this.handleScroll);
            document.removeEventListener('focusin', this.handleFocusIn);
            document.removeEventListener('focusout', this.handleFocusOut);
            window.removeEventListener('beforeunload', this.flush);
            
            // Flush remaining events
            this.flush();
            
            this.log('Tracker destroyed');
        }

        /**
         * Log messages if debug is enabled
         */
        log(message, data = null) {
            if (this.config.debug) {
                console.log(`[BotDetection] ${message}`, data);
            }
        }
    }

    // Expose to global scope
    window.BotDetection = {
        Tracker: BotDetectionTracker,
        
        // Convenience method for quick initialization
        init: function(config) {
            const tracker = new BotDetectionTracker(config);
            tracker.init();
            return tracker;
        },
        
        // Get current session ID
        getSessionId: function() {
            return window.botDetectionTracker?.sessionId;
        }
    };

})(window); 