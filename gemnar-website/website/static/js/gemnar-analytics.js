/**
 * Gemnar Analytics - Website Tracking Script
 * Provides comprehensive user behavior analytics including:
 * - Page views and sessions
 * - Mouse movements and clicks
 * - Form interactions
 * - Scroll tracking
 * - Session recordings
 */

(function (window, document) {
  "use strict";

  // Configuration
  const config = {
    apiEndpoint: window.GemnarAnalytics?.apiEndpoint || "/api/analytics",
    trackingCode: window.GemnarAnalytics?.trackingCode || null,
    sampleRate: window.GemnarAnalytics?.sampleRate || 1.0,
    recordMouse: window.GemnarAnalytics?.recordMouse !== false,
    recordClicks: window.GemnarAnalytics?.recordClicks !== false,
    recordScrolls: window.GemnarAnalytics?.recordScrolls !== false,
    recordForms: window.GemnarAnalytics?.recordForms !== false,
    debug: window.GemnarAnalytics?.debug || false,
  };

  // State
  let state = {
    sessionId: null,
    pageViewId: null,
    isTracking: false,
    mouseEvents: [],
    lastMouseEvent: null,
    scrollDepth: 0,
    clickCount: 0,
    formInteractions: 0,
    startTime: Date.now(),
    lastActivityTime: Date.now(),
  };

  // Utility functions
  function generateId() {
    // Generate a proper UUID v4
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      },
    );
  }

  function getSessionId() {
    let sessionId = sessionStorage.getItem("gemnar_session_id");
    if (!sessionId) {
      sessionId = generateId();
      sessionStorage.setItem("gemnar_session_id", sessionId);
    }
    return sessionId;
  }

  function getViewportSize() {
    return {
      width: window.innerWidth || document.documentElement.clientWidth,
      height: window.innerHeight || document.documentElement.clientHeight,
    };
  }

  function getScreenSize() {
    return {
      width: screen.width,
      height: screen.height,
    };
  }

  function getScrollDepth() {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    return Math.round(((scrollTop + windowHeight) / documentHeight) * 100);
  }

  function throttle(func, delay) {
    let timeoutId;
    let lastExecTime = 0;
    return function (...args) {
      const currentTime = Date.now();

      if (currentTime - lastExecTime > delay) {
        func.apply(this, args);
        lastExecTime = currentTime;
      } else {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(
          () => {
            func.apply(this, args);
            lastExecTime = Date.now();
          },
          delay - (currentTime - lastExecTime),
        );
      }
    };
  }

  function compress(data) {
    // Simple compression - in production, use a real compression library
    return JSON.stringify(data);
  }

  function sendData(endpoint, data) {
    if (!config.trackingCode) {
      if (config.debug)
        console.warn("Gemnar Analytics: No tracking code provided");
      return Promise.reject("No tracking code");
    }

    const payload = {
      tracking_code: config.trackingCode,
      ...data,
    };

    if (config.debug) {
      console.log("Gemnar Analytics: Sending data", endpoint, payload);
    }

    // Use fetch for pageview to get the response, sendBeacon for others
    const url = config.apiEndpoint + endpoint;
    const body = JSON.stringify(payload);

    if (endpoint === "/pageview") {
      return fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: body,
      }).then((response) => response.json());
    } else {
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: "application/json" });
        navigator.sendBeacon(url, blob);
      } else {
        fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: body,
          keepalive: true,
        }).catch((err) => {
          if (config.debug)
            console.error("Gemnar Analytics: Error sending data", err);
        });
      }
      return Promise.resolve();
    }
  }

  // Event tracking functions
  function trackPageView() {
    const viewport = getViewportSize();
    const screen = getScreenSize();

    const pageViewData = {
      session_id: state.sessionId,
      url: window.location.href,
      title: document.title,
      path: window.location.pathname,
      query_params: window.location.search,
      referrer: document.referrer,
      viewport_width: viewport.width,
      viewport_height: viewport.height,
      screen_width: screen.width,
      screen_height: screen.height,
      user_agent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    // Send pageview and get the page_view_id from the server
    sendData("/pageview", pageViewData)
      .then((response) => {
        if (response && response.page_view_id) {
          state.pageViewId = response.page_view_id;
        } else {
          // Fallback to generating ID if server doesn't return one
          state.pageViewId = generateId();
        }
      })
      .catch((err) => {
        if (config.debug) {
          console.error("Gemnar Analytics: Error tracking pageview", err);
        }
        // Fallback to generating ID on error
        state.pageViewId = generateId();
      });

    // Reset page-specific state
    state.startTime = Date.now();
    state.scrollDepth = 0;
    state.clickCount = 0;
    state.formInteractions = 0;
    state.mouseEvents = [];
  }

  function trackEvent(eventType, data = {}, retryCount = 0) {
    if (!state.pageViewId) {
      // Queue the event if pageViewId is not ready yet (max 10 retries)
      if (retryCount < 10) {
        setTimeout(() => trackEvent(eventType, data, retryCount + 1), 100);
      } else if (config.debug) {
        console.warn(
          "Gemnar Analytics: Failed to track event, no pageViewId available",
          eventType,
        );
      }
      return;
    }

    const eventData = {
      page_view_id: state.pageViewId,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      ...data,
    };

    sendData("/event", eventData);
  }

  function trackMouseMovement(event) {
    if (!config.recordMouse || !state.pageViewId) return;

    const now = Date.now();
    const mouseData = {
      x: event.clientX,
      y: event.clientY,
      timestamp: now - state.startTime,
    };

    state.mouseEvents.push(mouseData);
    state.lastMouseEvent = mouseData;
    state.lastActivityTime = now;

    // Batch mouse events and send every 5 seconds
    if (state.mouseEvents.length >= 50) {
      sendMouseData();
    }
  }

  function sendMouseData() {
    if (state.mouseEvents.length === 0 || !state.pageViewId) return;

    const recordingData = {
      page_view_id: state.pageViewId,
      mouse_movements: compress(state.mouseEvents),
      recording_duration: Date.now() - state.startTime,
    };

    sendData("/recording", recordingData);
    state.mouseEvents = [];
  }

  function trackClick(event) {
    if (!config.recordClicks) return;

    state.clickCount++;
    const element = event.target;

    const clickData = {
      element_tag: element.tagName.toLowerCase(),
      element_classes: element.className,
      element_id: element.id,
      element_text: element.textContent?.substring(0, 100),
      x_coordinate: event.clientX,
      y_coordinate: event.clientY,
    };

    trackEvent("click", clickData);
  }

  function trackScroll() {
    if (!config.recordScrolls) return;

    const currentScrollDepth = getScrollDepth();
    if (currentScrollDepth > state.scrollDepth) {
      state.scrollDepth = currentScrollDepth;
    }

    state.lastActivityTime = Date.now();
  }

  function trackFormInteraction(event) {
    if (!config.recordForms) return;

    state.formInteractions++;

    const formData = {
      element_tag: event.target.tagName.toLowerCase(),
      element_type: event.target.type,
      element_name: event.target.name,
      element_id: event.target.id,
    };

    trackEvent("form_focus", formData);
  }

  function trackFormSubmit(event) {
    if (!config.recordForms) return;

    const formData = {
      element_tag: "form",
      element_id: event.target.id,
      element_classes: event.target.className,
    };

    trackEvent("form_submit", formData);
  }

  function trackError(error, source, lineno, colno) {
    const errorData = {
      error_message: error.toString(),
      source: source,
      line: lineno,
      column: colno,
    };

    trackEvent("error", errorData);
  }

  // Session management
  function updatePageMetrics() {
    if (!state.pageViewId) return;

    const duration = Math.round((Date.now() - state.startTime) / 1000);

    const metricsData = {
      page_view_id: state.pageViewId,
      duration_seconds: duration,
      scroll_depth_percentage: state.scrollDepth,
      clicks_count: state.clickCount,
      form_interactions: state.formInteractions,
    };

    sendData("/metrics", metricsData);
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      // Page is hidden, send any pending data
      sendMouseData();
      updatePageMetrics();
    } else {
      // Page is visible again, update activity time
      state.lastActivityTime = Date.now();
    }
  }

  function handleBeforeUnload() {
    sendMouseData();
    updatePageMetrics();
  }

  // Initialize tracking
  function init() {
    // Check if should track (sampling)
    if (Math.random() > config.sampleRate) {
      if (config.debug)
        console.log("Gemnar Analytics: Skipped due to sampling");
      return;
    }

    if (!config.trackingCode) {
      console.error("Gemnar Analytics: No tracking code provided");
      return;
    }

    state.sessionId = getSessionId();
    state.isTracking = true;

    // Track initial page view
    trackPageView();

    // Set up event listeners
    if (config.recordMouse) {
      document.addEventListener("mousemove", throttle(trackMouseMovement, 100));
    }

    if (config.recordClicks) {
      document.addEventListener("click", trackClick);
    }

    if (config.recordScrolls) {
      window.addEventListener("scroll", throttle(trackScroll, 250));
    }

    if (config.recordForms) {
      document.addEventListener(
        "focus",
        function (event) {
          if (
            event.target.tagName === "INPUT" ||
            event.target.tagName === "TEXTAREA" ||
            event.target.tagName === "SELECT"
          ) {
            trackFormInteraction(event);
          }
        },
        true,
      );

      document.addEventListener("submit", trackFormSubmit);
    }

    // Error tracking
    window.addEventListener("error", function (event) {
      trackError(event.error, event.filename, event.lineno, event.colno);
    });

    // Page lifecycle events
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handleBeforeUnload);

    // Send mouse data periodically
    setInterval(sendMouseData, 5000);

    // Send metrics periodically
    setInterval(updatePageMetrics, 30000);

    if (config.debug) {
      console.log("Gemnar Analytics: Initialized", {
        sessionId: state.sessionId,
        trackingCode: config.trackingCode,
      });
    }
  }

  // Handle SPAs (Single Page Applications)
  function handleSPANavigation() {
    // Track new page view for SPAs
    trackPageView();
  }

  // Expose public API
  window.GemnarAnalytics = window.GemnarAnalytics || {};
  window.GemnarAnalytics.trackEvent = trackEvent;
  window.GemnarAnalytics.trackPageView = handleSPANavigation;

  // Auto-initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window, document);
