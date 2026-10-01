/**
 * Dashboard strategy for the Schwörer Climate Control integration.
 *
 * Builds the dashboard from the entity registry at render time, so a room added
 * later appears without anyone editing a dashboard. Two views: an overview with
 * the controls, and a debug view laying out the decision behind the unit and
 * behind every room.
 *
 * Deliberately built from Home Assistant's own cards. The decision records are
 * rendered by markdown cards reading the sensors' attributes, so this ships no
 * custom card and does not compete with a card repository of its own.
 *
 * Use it with:
 *
 *   strategy:
 *     type: custom:schwoerer-climate-control
 *
 * or, for one view inside a dashboard you already have:
 *
 *   views:
 *     - strategy:
 *         type: custom:schwoerer-climate-control
 *         view: debug
 */

const DOMAIN = "schwoerer_climate_control";

const LABELS = {
  en: {
    title: "Climate Control",
    overview: "Overview",
    debug: "Debug",
    controls: "Controls",
    status: "Status",
    rooms: "Rooms",
    missing: [
      "## Not set up yet",
      "",
      "Add the integration under **Settings → Devices & Services**, then add a",
      "room to it. This dashboard fills itself in.",
    ].join("\n"),
    conditions: "Conditions",
    readings: "Readings",
    settings: "Settings",
    yes: "yes",
    no: "no",
    notReporting: "not reporting",
    contacts: "contacts",
    allClosed: "all closed",
    oneOpen: "one open",
    noData: "No decision yet.",
    from: "from",
  },
  de: {
    title: "Klimasteuerung",
    overview: "Übersicht",
    debug: "Debug",
    controls: "Steuerung",
    status: "Status",
    rooms: "Räume",
    missing: [
      "## Noch nicht eingerichtet",
      "",
      "Füge die Integration unter **Einstellungen → Geräte & Dienste** hinzu und",
      "dann einen Raum. Dieses Dashboard füllt sich selbst.",
    ].join("\n"),
    conditions: "Bedingungen",
    readings: "Messwerte",
    settings: "Einstellungen",
    yes: "ja",
    no: "nein",
    notReporting: "meldet nichts",
    contacts: "Kontakte",
    allClosed: "alle zu",
    oneOpen: "eines offen",
    noData: "Noch keine Entscheidung.",
    from: "von",
  },
};

function labels(hass) {
  const language = (hass && hass.language) || "en";
  return LABELS[language.split("-")[0]] || LABELS.en;
}

/**
 * Every entity of this integration, grouped into the hub and the rooms.
 *
 * The hub is the device that carries the switches. A decision sensor is any of
 * our sensors whose state has a message attribute, which survives a rename in a
 * way an entity id suffix would not.
 */
function collect(hass) {
  const entities = Object.values(hass.entities || {}).filter(
    (entry) => entry.platform === DOMAIN && entry.device_id,
  );

  const byDevice = new Map();
  for (const entry of entities) {
    if (!byDevice.has(entry.device_id)) byDevice.set(entry.device_id, []);
    byDevice.get(entry.device_id).push(entry.entity_id);
  }

  let hub = null;
  const rooms = [];
  for (const [deviceId, ids] of byDevice) {
    const device = (hass.devices || {})[deviceId];
    if (!device) continue;
    const name = device.name_by_user || device.name || "";
    const group = { name, ids: ids.slice().sort() };
    if (ids.some((id) => id.startsWith("switch."))) {
      hub = group;
    } else {
      rooms.push(group);
    }
  }
  rooms.sort((a, b) => a.name.localeCompare(b.name));
  return { hub, rooms };
}

function isDecision(hass, entityId) {
  const state = hass.states[entityId];
  return Boolean(state && state.attributes && "message" in state.attributes);
}

function ofDomain(ids, ...domains) {
  return ids.filter((id) => domains.includes(id.split(".")[0]));
}

/** The one line that answers what the controller is doing right now. */
function headline(entityId, t) {
  return {
    type: "markdown",
    content: [
      `{% set e = '${entityId}' %}`,
      `{% if state_attr(e, 'message') %}`,
      `### {{ states(e) | capitalize }}`,
      `{{ state_attr(e, 'message') }}`,
      `{% else %}${t.noData}{% endif %}`,
    ].join("\n"),
  };
}

/**
 * The decision behind one sensor, in full.
 *
 * Reading it out of the attributes rather than out of a bespoke card is what
 * keeps this dashboard made of stock parts.
 */
function decisionCard(hass, entityId, t) {
  const state = hass.states[entityId];
  const name = (state && state.attributes.friendly_name) || entityId;
  return {
    type: "markdown",
    content: [
      `{% set e = '${entityId}' %}`,
      `### ${name}`,
      `**{{ states(e) | capitalize }}**`,
      ``,
      `{{ state_attr(e, 'message') or '${t.noData}' }}`,
      ``,
      `{% set gates = state_attr(e, 'gates') or [] %}`,
      `{% if gates %}**${t.conditions}**`,
      `{% for gate in gates %}`,
      `- {{ gate.name }}: {{ '${t.yes}' if gate.passed else '${t.no}' }}` +
        `{% if gate.detail %} ({{ gate.detail }}){% endif %}`,
      `{% endfor %}{% endif %}`,
      ``,
      `{% set inputs = state_attr(e, 'inputs') or {} %}`,
      `{% if inputs %}**${t.readings}**`,
      `{% for key, value in inputs.items() if value is not none %}`,
      `{% if value is sequence and value is not mapping and value is not string %}`,
      `- ${t.contacts}: {{ '${t.oneOpen}' if value | selectattr('value') | list | count` +
        ` else '${t.allClosed}' }}`,
      `{% else %}`,
      `- {{ key }}: {{ value.value }}` +
        `{% if not value.ok %} (${t.notReporting}){% endif %}`,
      `{% endif %}`,
      `{% endfor %}{% endif %}`,
      ``,
      `{% set settings = state_attr(e, 'settings') or {} %}`,
      `{% if settings %}**${t.settings}**`,
      `{% for key, value in settings.items() %}`,
      `- {{ key }}: {{ value.value }} (${t.from} {{ value.source }})`,
      `{% endfor %}{% endif %}`,
    ].join("\n"),
  };
}

function overviewView(hass, hub, rooms, t) {
  const cards = [];

  if (hub) {
    const decisions = ofDomain(hub.ids, "sensor").filter((id) =>
      isDecision(hass, id),
    );
    if (decisions.length) cards.push(headline(decisions[0], t));

    const controls = ofDomain(hub.ids, "switch", "select", "button", "number");
    if (controls.length) {
      cards.push({ type: "entities", title: t.controls, entities: controls });
    }

    const status = ofDomain(hub.ids, "sensor", "binary_sensor");
    if (status.length) {
      cards.push({ type: "entities", title: t.status, entities: status });
    }
  }

  const roomEntities = rooms.flatMap((room) => room.ids);
  if (roomEntities.length) {
    cards.push({
      type: "entities",
      title: t.rooms,
      entities: roomEntities.map((id) => ({
        entity: id,
        secondary_info: "last-changed",
      })),
    });
  }

  return { title: t.overview, path: "overview", cards };
}

function debugView(hass, hub, rooms, t) {
  const ids = [
    ...(hub ? ofDomain(hub.ids, "sensor") : []),
    ...rooms.flatMap((room) => ofDomain(room.ids, "sensor")),
  ].filter((id) => isDecision(hass, id));

  return {
    title: t.debug,
    path: "debug",
    cards: ids.map((id) => decisionCard(hass, id, t)),
  };
}

function generateViews(hass) {
  const t = labels(hass);
  const { hub, rooms } = collect(hass);

  if (!hub && rooms.length === 0) {
    return [
      {
        title: t.overview,
        path: "overview",
        cards: [{ type: "markdown", content: t.missing }],
      },
    ];
  }

  return [overviewView(hass, hub, rooms, t), debugView(hass, hub, rooms, t)];
}

class ClimateControlDashboardStrategy extends HTMLElement {
  static async generate(_config, hass) {
    return { title: labels(hass).title, views: generateViews(hass) };
  }
}

class ClimateControlViewStrategy extends HTMLElement {
  static async generate(config, hass) {
    const views = generateViews(hass);
    const wanted = config && config.view === "debug" ? "debug" : "overview";
    const view = views.find((one) => one.path === wanted) || views[0];
    return { ...view, title: undefined, path: undefined };
  }
}

// The frontend looks a strategy up by these exact tag names, derived from the
// `type: custom:schwoerer-climate-control` it is asked for.
const ELEMENTS = {
  "ll-strategy-dashboard-schwoerer-climate-control":
    ClimateControlDashboardStrategy,
  "ll-strategy-view-schwoerer-climate-control": ClimateControlViewStrategy,
};

function register(registry) {
  for (const [tag, element] of Object.entries(ELEMENTS)) {
    if (!registry.get(tag)) registry.define(tag, element);
  }
}

// The frontend may swap the custom element registry out from under an extra
// module while it boots, and a strategy registered in the old one is a strategy
// the dashboard can never find. So register now, and keep registering into
// whatever window.customElements is until the frontend's own <home-assistant>
// element turns up in it: from then on that registry is the one being used.
// Same reasoning as the cover-control strategy, which hit this first.
const SETTLE_TIMEOUT_MS = 60000;
const started = Date.now();
(function registerUntilSettled() {
  register(window.customElements);
  const settled = window.customElements.get("home-assistant");
  if (!settled && Date.now() - started < SETTLE_TIMEOUT_MS) {
    setTimeout(registerUntilSettled, 25);
  }
})();
