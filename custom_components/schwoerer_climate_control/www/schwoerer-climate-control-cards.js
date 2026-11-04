/**
 * Cards for the Schwörer Climate Control dashboard.
 *
 * They answer what state the house is in and why, never how to change it: the
 * controller is meant to run on its own. Every rule lives in the integration;
 * the decision sensors publish how close each one is to changing (`thresholds`,
 * `upcoming`) and which entities they read (`sources`), and these cards only
 * put that, and the recorder's history, into words and pictures.
 *
 * Plain custom elements without a build step. Colours come from the active
 * theme where it has one, so the cards follow it into dark mode.
 */

const DOMAIN = "schwoerer_climate_control";

////////////////////////////////////////////////////////////////////////////////
// Words

const WORDS = {
  de: {
    heatPump: "Wärmepumpe",
    heatPumpLead: "Freigabe entscheidet der Controller, ob sie läuft, die WGT",
    releasedFor: "Wofür freigegeben",
    whatAndWhy: "Was sie tut, und warum",
    howClose: "Wie nah am nächsten Wechsel",
    today: "Heute",
    heat: "Heizen",
    cool: "Kühlen",
    fn: "Funktion",
    free: "frei",
    locked: "gesperrt",
    held: "gehalten",
    off: "aus",
    on: "an",
    nothing: "nichts",
    none: "keine",
    heating: "Heizt",
    cooling: "Kühlt",
    idle: "Steht",
    since: (t) => `seit ${t}`,
    todayHours: (h) => `heute ${h}`,
    deviceDecides: "Start und Stopp entscheidet die WGT.",
    stageOneObserved: "Bei Luftstufe 1 hat sie bisher nicht geheizt.",
    legendHeats: "heizt",
    legendNight: "Nacht",
    legendStage3: "Luftstufe 3",
    now: "jetzt",
    aux: "Zuheizer",
    auxHouseOn: "Haus-Freigabe an",
    auxHouseOff: "Haus-Freigabe aus: kein Raum braucht gerade einen",
    mayRun: "Dürfen sie laufen",
    yesAll: "Ja, in allen Räumen",
    noneMay: "Nein, in keinem Raum",
    someMay: (n, of) => `In ${n} von ${of} Räumen`,
    room: "Raum",
    actualTarget: "Ist / Soll",
    may: "Darf",
    runs: "Zustand",
    nextChange: "Nächster Wechsel",
    mayYes: "darf",
    mayNo: "gesperrt",
    tooCold: (k) => `${k} zu kalt`,
    tooWarm: (k) => `${k} zu warm`,
    atTarget: "auf Soll",
    health: "Läuft die Anlage gut?",
    energy: "Energie",
    energyNow: "Jetzt",
    energyToday: "Heute",
    energyWeek: "7 Tage",
    energyLastYear: "Vorjahr",
    perDay: (v) => `Ø ${v}/Tag`,
    noData: "keine Daten",
    noPower: "Wähle unter Einstellungen → Entitäten die Leistung der Anlage, dann steht hier ihr Verbrauch.",
    daysChart: "kWh pro Tag, letzte 14 Tage",
    normalised: (v) => `bereinigt: ${v} kWh je K·Tag`,
    lastYearSame: (v) => `gleiche Woche: ${v}`,
    roomsBelow: "Räume unter Soll",
    roomsAbove: "Räume über Soll",
    houseExtract: "Haus (Abluft)",
    hpToday: "Wärmepumpe",
    auxToday: "Zuheizer",
    sinceDays: (k, d) => `${k} seit ${d}`,
    nightZero: (h) => `heute, nachts ${h}`,
    verdictGood: "Läuft gut",
    verdictCatching: "Holt auf",
    verdictBehind: "Fällt langsam zurück",
    verdictCool: "Bleibt kühl",
    verdictWarm: "Wird zu warm",
    verdictAir: "Luft ist gut",
    verdictAirBad: "Luft wird schlecht",
    leadGood: "Alle Räume sind auf Soll, das Haus hält seine Temperatur.",
    leadCatching: "Einzelne Räume liegen unter Soll, das Haus wird aber wärmer.",
    leadBehind: (k, d) => `Das Haus hat seit ${d} ${k} verloren.`,
    leadBehindRooms: "Räume liegen unter Soll und holen nicht auf.",
    leadCool: "Kein Raum über seinem Kühl-Soll.",
    leadWarm: "Räume liegen über ihrem Kühl-Soll.",
    leadAir: "CO₂ und Feuchte in allen Räumen unter den Grenzen.",
    leadAirBad: "In einzelnen Räumen sind CO₂ oder Feuchte hoch.",
    inShort: "Kurz gesagt",
    causes: "Mögliche Ursachen",
    auxPath: "Zuheizer: der Weg zum Einschalten",
    whatNext: "Was als Nächstes passiert",
    last24: "Letzte 24 Stunden",
    roomLine: "Raum",
    targetLine: "Soll",
    tagYes: "trifft zu",
    tagPart: "teils",
    tagNo: "nein",
    tagWaits: "wartet",
    tagUnknown: "nicht messbar",
    back: "Übersicht",
    houseCold: "Ist es im Haus zu kalt?",
    houseWarm: "Ist es im Haus zu warm?",
    coldest: "Kältester Raum",
    warmest: "Wärmster Raum",
    outdoor: "Draußen",
    heatIn: "Kommt genug Wärme rein?",
    heatOut: "Geht zu viel raus?",
    goals: "Sind die Ziele zu niedrig?",
    heatingQ: "Wird geheizt?",
    removedQ: "Wird Wärme abgeführt?",
    balance: "Wärmebilanz der letzten 7 Tage",
    balanceNote: "Oben die mittlere Abluft, der Balken zeigt die Stunden, die die Wärmepumpe geheizt hat, von 24.",
    chronicle: "Was hat sich geändert, und warum?",
    chronicleLead: "Letzte 24 Stunden: was der Controller getan hat, was die WGT selbst getan hat, und was von außen kam.",
    byController: "Controller",
    byDevice: "WGT selbst",
    byOutside: "Von außen",
    device: "Läuft das Gerät technisch sauber?",
    deviceOk: "Ja. Keine Fehlermeldung, die Ventilatoren laufen gleich stark, alle Werte sind übernommen.",
    deviceNotOk: "Nicht ganz, siehe unten.",
    airPath: "Weg der Luft",
    airPathLead: "Wo die Wärme herkommt und wohin sie geht",
    freshAir: "Frischluft in die Räume",
    exhaustAir: "Abluft aus den Räumen",
    fault: "Fehlermeldung",
    operation: "Betriebsart",
    fans: "Ventilatoren",
    recovery: "Wärmerückgewinnung",
    filter: "Filter",
    controller: "Controller",
    allTaken: "alles übernommen",
    notTaken: (n) => `${n} nicht übernommen`,
    allInputs: "alle Eingänge melden",
    missingInputs: (n) => `${n} Eingänge fehlen`,
    remaining: "Restlaufzeit",
    mustBeManual: "so muss sie stehen",
    notManual: "muss auf Manuell stehen",
    bypassClosed: "Bypass zu",
    bypassOpen: "Bypass offen",
    days: (d) => `${d} Tage`,
    noFault: "keine",
    stages: {
      outdoor: "Außen",
      t2: "Vorheizregister",
      t3: "nach Wärmetauscher",
      t8: "Kondensator",
      t4: "Zuluft",
      t5: "Abluft",
      t6: "nach Wärmetauscher",
      t7: "Verdampfer",
    },
    gainNote: (wt, hp) => `Der Wärmetauscher holt ${wt} aus der Abluft${hp ? `, der Kondensator der Wärmepumpe weitere ${hp}` : ""}.`,
    evaporatorNote: "Unter 0 °C kann der Verdampfer vereisen, das wäre hier zu sehen.",
    air: "Luft",
    airLead: "CO₂ und Feuchte je Raum",
    fanStage: "Lüftungsstufe",
    co2: "CO₂",
    humidity: "Feuchte",
    noAirSensors: "Keinem Raum ist ein CO₂- oder Feuchtesensor zugeordnet.",
    coolingTitle: "Kühlung",
    nightCooling: "Nachtauskühlung",
    heatProtection: "Hitzeschutz",
    alerts: "Braucht Aufmerksamkeit",
    alertMissing: (list) => `Eingänge fehlen: ${list}`,
    alertStuck: (list) => `Wird nicht übernommen: ${list}`,
    alertManual: (mode) => `Die WGT steht auf „${mode}“, die Steuerung braucht „Manuell“.`,
    alertFault: (code) => `Die WGT meldet Fehler ${code}.`,
    alertFrost: "Frostschutz ist aktiv.",
    alertDisabled: "Der Controller ist ausgeschaltet, es wird nichts geschrieben.",
    alertDryRun: "Probelauf: Der Controller entscheidet, schreibt aber nichts.",
    more: "Mehr",
    windows: "Fenster",
    outdoorCold: "Draußen kalt genug",
    belowLimit: (v, l) => `${v}, unter ${l}`,
    lockedFrom: (l, d) => `gesperrt ab ${l}, noch ${d}`,
    nightGate: "Nachts",
    offAtNight: (names) => `aus in ${names}`,
    noneOffAtNight: "in keinem Raum aus",
    allClosed: "alle zu",
    linkCold: "Haus zu kalt?",
    linkWarm: "Haus zu warm?",
    linkChronicle: "Chronik",
    linkDevice: "Gerät",
    linkDebug: "Alle Details",
    loading: "lädt …",
    hours: (h) => `${h} h`,
    inTime: (t) => `in ${t}`,
    atTime: (t) => `um ${t}`,
    minutes: (m) => `${m} min`,
    hoursMinutes: (h, m) => `${h} h ${m} min`,
    stillToGo: (v) => `noch ${v}`,
    passed: "erreicht",
  },
  en: {
    heatPump: "Heat pump",
    heatPumpLead: "The controller decides the release, the unit decides whether it runs",
    releasedFor: "Released for",
    whatAndWhy: "What it does, and why",
    howClose: "How close the next change is",
    today: "Today",
    heat: "Heating",
    cool: "Cooling",
    fn: "Function",
    free: "released",
    locked: "locked",
    held: "held",
    off: "off",
    on: "on",
    nothing: "nothing",
    none: "none",
    heating: "Heating",
    cooling: "Cooling",
    idle: "Idle",
    since: (t) => `since ${t}`,
    todayHours: (h) => `today ${h}`,
    deviceDecides: "The unit decides when it starts and stops.",
    stageOneObserved: "At fan level 1 it has not heated so far.",
    legendHeats: "heating",
    legendNight: "night",
    legendStage3: "fan level 3",
    now: "now",
    aux: "Auxiliary heaters",
    auxHouseOn: "House release on",
    auxHouseOff: "House release off: no room needs one right now",
    mayRun: "May they run",
    yesAll: "Yes, in every room",
    noneMay: "No, in no room",
    someMay: (n, of) => `In ${n} of ${of} rooms`,
    room: "Room",
    actualTarget: "Actual / target",
    may: "May",
    runs: "State",
    nextChange: "Next change",
    mayYes: "may",
    mayNo: "locked",
    tooCold: (k) => `${k} too cold`,
    tooWarm: (k) => `${k} too warm`,
    atTarget: "at target",
    health: "Is the system doing well?",
    energy: "Energy",
    energyNow: "Now",
    energyToday: "Today",
    energyWeek: "7 days",
    energyLastYear: "Last year",
    perDay: (v) => `avg ${v}/day`,
    noData: "no data",
    noPower: "Pick the power of the unit under Settings → Entities, and its consumption shows here.",
    daysChart: "kWh per day, last 14 days",
    normalised: (v) => `normalised: ${v} kWh per K·day`,
    lastYearSame: (v) => `same week: ${v}`,
    roomsBelow: "Rooms below target",
    roomsAbove: "Rooms above target",
    houseExtract: "House (extract)",
    hpToday: "Heat pump",
    auxToday: "Aux heaters",
    sinceDays: (k, d) => `${k} since ${d}`,
    nightZero: (h) => `today, at night ${h}`,
    verdictGood: "Doing well",
    verdictCatching: "Catching up",
    verdictBehind: "Slowly falling behind",
    verdictCool: "Staying cool",
    verdictWarm: "Getting too warm",
    verdictAir: "Air is good",
    verdictAirBad: "Air is getting stale",
    leadGood: "Every room is at target, the house holds its temperature.",
    leadCatching: "Some rooms are below target, but the house is getting warmer.",
    leadBehind: (k, d) => `The house has lost ${k} since ${d}.`,
    leadBehindRooms: "Rooms are below target and not catching up.",
    leadCool: "No room is above its cooling target.",
    leadWarm: "Rooms are above their cooling target.",
    leadAir: "CO₂ and humidity are below the limits in every room.",
    leadAirBad: "CO₂ or humidity is high in some rooms.",
    inShort: "In short",
    causes: "Possible causes",
    auxPath: "Auxiliary heater: the way to switching on",
    whatNext: "What happens next",
    last24: "Last 24 hours",
    roomLine: "Room",
    targetLine: "Target",
    tagYes: "applies",
    tagPart: "partly",
    tagNo: "no",
    tagWaits: "waiting",
    tagUnknown: "not measured",
    back: "Overview",
    houseCold: "Is the house too cold?",
    houseWarm: "Is the house too warm?",
    coldest: "Coldest room",
    warmest: "Warmest room",
    outdoor: "Outdoor",
    heatIn: "Is enough heat coming in?",
    heatOut: "Is too much going out?",
    goals: "Are the targets too low?",
    heatingQ: "Is anything heating?",
    removedQ: "Is heat being removed?",
    balance: "Heat balance of the last 7 days",
    balanceNote: "On top the mean extract air, the bar shows the hours the heat pump heated, out of 24.",
    chronicle: "What changed, and why?",
    chronicleLead: "Last 24 hours: what the controller did, what the unit did on its own, and what came from outside.",
    byController: "Controller",
    byDevice: "Unit itself",
    byOutside: "From outside",
    device: "Is the unit running cleanly?",
    deviceOk: "Yes. No fault, both fans run alike, every value has been taken.",
    deviceNotOk: "Not entirely, see below.",
    airPath: "Path of the air",
    airPathLead: "Where the heat comes from and where it goes",
    freshAir: "Fresh air into the rooms",
    exhaustAir: "Extract air from the rooms",
    fault: "Fault",
    operation: "Operating mode",
    fans: "Fans",
    recovery: "Heat recovery",
    filter: "Filter",
    controller: "Controller",
    allTaken: "everything taken",
    notTaken: (n) => `${n} not taken`,
    allInputs: "every input reports",
    missingInputs: (n) => `${n} inputs missing`,
    remaining: "remaining",
    mustBeManual: "as it has to be",
    notManual: "has to be on manual",
    bypassClosed: "bypass closed",
    bypassOpen: "bypass open",
    days: (d) => `${d} days`,
    noFault: "none",
    stages: {
      outdoor: "Outdoor",
      t2: "Preheating coil",
      t3: "after exchanger",
      t8: "Condenser",
      t4: "Supply air",
      t5: "Extract air",
      t6: "after exchanger",
      t7: "Evaporator",
    },
    gainNote: (wt, hp) => `The exchanger recovers ${wt} from the extract air${hp ? `, the heat pump's condenser adds ${hp}` : ""}.`,
    evaporatorNote: "Below 0 °C the evaporator can ice up, which would show here.",
    air: "Air",
    airLead: "CO₂ and humidity per room",
    fanStage: "Fan level",
    co2: "CO₂",
    humidity: "Humidity",
    noAirSensors: "No room has a CO₂ or humidity sensor.",
    coolingTitle: "Cooling",
    nightCooling: "Night cooling",
    heatProtection: "Heat protection",
    alerts: "Needs attention",
    alertMissing: (list) => `Inputs missing: ${list}`,
    alertStuck: (list) => `Not taken: ${list}`,
    alertManual: (mode) => `The unit is on "${mode}", the controller needs "manual".`,
    alertFault: (code) => `The unit reports fault ${code}.`,
    alertFrost: "Frost protection is active.",
    alertDisabled: "The controller is off, nothing is written.",
    alertDryRun: "Dry run: the controller decides but writes nothing.",
    more: "More",
    windows: "Windows",
    outdoorCold: "Cold enough outdoors",
    belowLimit: (v, l) => `${v}, below ${l}`,
    lockedFrom: (l, d) => `locked from ${l}, ${d} to go`,
    nightGate: "At night",
    offAtNight: (names) => `off in ${names}`,
    noneOffAtNight: "off in no room",
    allClosed: "all closed",
    linkCold: "House too cold?",
    linkWarm: "House too warm?",
    linkChronicle: "Chronicle",
    linkDevice: "Unit",
    linkDebug: "All details",
    loading: "loading …",
    hours: (h) => `${h} h`,
    inTime: (t) => `in ${t}`,
    atTime: (t) => `at ${t}`,
    minutes: (m) => `${m} min`,
    hoursMinutes: (h, m) => `${h} h ${m} min`,
    stillToGo: (v) => `${v} to go`,
    passed: "reached",
  },
};

/** What a threshold or an upcoming event means, in a title and a rule. */
const OUTLOOK = {
  de: {
    heat_release_off: ["Freigabe endet", (t) => `ab ${t.limit} draußen, jetzt ${t.value} (mit Hysterese)`],
    heat_release_on: ["Freigabe beginnt", (t) => `unter ${t.limit} draußen, jetzt ${t.value}`],
    forecast_counts: ["Prognose zählt", (t) => `erst ab ${t.limit} draußen, jetzt ${t.value}`],
    forecast_blocks: ["Prognose sperrt", (t) => `Höchstwert ab ${t.limit}, heute ${t.value}`],
    aux_outdoor: ["Zuheizer gesperrt", (t) => `ab ${t.limit} draußen, jetzt ${t.value}`],
    fan_heat_cap: ["Lüftung gedrosselt", (t) => `ab ${t.limit} wärmer draußen als in der Abluft, jetzt ${t.value}`],
    fan_off: ["Lüftung steht", (t) => `ab ${t.limit} wärmer draußen als in der Abluft, jetzt ${t.value}`],
    cool_release_on: ["Kühlen beginnt", (t) => `ab ${t.limit} im wärmsten Raum, jetzt ${t.value}`],
    cool_release_off: ["Kühlen endet", (t) => `unter ${t.limit} im wärmsten Raum, jetzt ${t.value}`],
    surplus_on: ["PV-Überschuss reicht", (t) => `ab ${t.limit}, jetzt ${t.value}`],
    aux_wanted: ["Zuheizer gewünscht", (t) => `ab ${t.limit} im Raum, jetzt ${t.value}`],
    aux_override: ["Zuluft zählt nicht mehr", (t) => `ab ${t.limit} im Raum, dann wartet der Zuheizer nur noch 15 min`],
    aux_supply: ["Zuluft reicht nicht", (t) => `unter ${t.limit} wärmer als der Raum, jetzt ${t.value}`],
    aux_rise: ["Raum holt auf", (t) => `${t.value} von nötigen ${t.limit} gestiegen`],
    aux_reached: ["Zuheizer fertig", (t) => `bei ${t.limit} im Raum, jetzt ${t.value}`],
    frost_protection: ["Frostschutz", (t) => `unter ${t.limit}, jetzt ${t.value}`],
    night_starts: ["Nacht beginnt", () => "Nachtwerte für Sollwert und Lüftung"],
    night_ends: ["Nacht endet", () => "Tageswerte für Sollwert und Lüftung"],
    release_lockout_ends: ["Sperrzeit endet", () => "dann darf die Freigabe wechseln"],
    aux_verdict: ["Urteil: holt der Raum auf?", () => "sonst beginnen die 15 min Wartezeit"],
    aux_on: ["Zuheizer an", () => "nach 15 min Wartezeit"],
  },
  en: {
    heat_release_off: ["Release ends", (t) => `from ${t.limit} outdoors, now ${t.value} (with hysteresis)`],
    heat_release_on: ["Release starts", (t) => `below ${t.limit} outdoors, now ${t.value}`],
    forecast_counts: ["Forecast counts", (t) => `only from ${t.limit} outdoors, now ${t.value}`],
    forecast_blocks: ["Forecast blocks", (t) => `high from ${t.limit}, today ${t.value}`],
    aux_outdoor: ["Aux heaters locked", (t) => `from ${t.limit} outdoors, now ${t.value}`],
    fan_heat_cap: ["Fan capped", (t) => `from ${t.limit} warmer outdoors than the extract air, now ${t.value}`],
    fan_off: ["Fan stops", (t) => `from ${t.limit} warmer outdoors than the extract air, now ${t.value}`],
    cool_release_on: ["Cooling starts", (t) => `from ${t.limit} in the warmest room, now ${t.value}`],
    cool_release_off: ["Cooling ends", (t) => `below ${t.limit} in the warmest room, now ${t.value}`],
    surplus_on: ["Enough PV surplus", (t) => `from ${t.limit}, now ${t.value}`],
    aux_wanted: ["Aux heater wanted", (t) => `from ${t.limit} in the room, now ${t.value}`],
    aux_override: ["Supply air stops counting", (t) => `from ${t.limit} in the room, then the heater only waits 15 min`],
    aux_supply: ["Supply air not enough", (t) => `below ${t.limit} above the room, now ${t.value}`],
    aux_rise: ["Room catching up", (t) => `risen ${t.value} of the ${t.limit} needed`],
    aux_reached: ["Aux heater done", (t) => `at ${t.limit} in the room, now ${t.value}`],
    frost_protection: ["Frost protection", (t) => `below ${t.limit}, now ${t.value}`],
    night_starts: ["Night starts", () => "night values for setpoint and fan"],
    night_ends: ["Night ends", () => "day values for setpoint and fan"],
    release_lockout_ends: ["Lockout ends", () => "then the release may change"],
    aux_verdict: ["Verdict: is the room catching up?", () => "otherwise the 15 min wait begins"],
    aux_on: ["Aux heater on", () => "after the 15 min wait"],
  },
};

function lang(hass) {
  const code = ((hass && (hass.locale?.language || hass.language)) || "en").split("-")[0];
  return WORDS[code] ? code : "en";
}

function words(hass) {
  return WORDS[lang(hass)];
}

////////////////////////////////////////////////////////////////////////////////
// Formatting

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function num(hass, value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
  return new Intl.NumberFormat(lang(hass), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

function withUnit(hass, value, unit, digits = 1) {
  if (value === null || value === undefined) return "–";
  const d = unit === "W" ? 0 : digits;
  return `${num(hass, value, d)} ${unit}`;
}

function clock(hass, date) {
  return new Intl.DateTimeFormat(lang(hass), {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: hass.config?.time_zone,
  }).format(date);
}

function dayLabel(hass, date) {
  return new Intl.DateTimeFormat(lang(hass), {
    day: "2-digit",
    month: "2-digit",
    timeZone: hass.config?.time_zone,
  }).format(date);
}

/** Since when, as a clock time today or a date before that. */
function sinceText(hass, date) {
  const now = new Date();
  const sameDay = dayLabel(hass, now) === dayLabel(hass, date);
  return sameDay ? clock(hass, date) : `${dayLabel(hass, date)} ${clock(hass, date)}`;
}

function duration(hass, ms) {
  const w = words(hass);
  const minutes = Math.max(0, Math.round(ms / 60000));
  if (minutes < 60) return w.minutes(minutes);
  return w.hoursMinutes(Math.floor(minutes / 60), minutes % 60);
}

function hoursText(hass, hours) {
  return words(hass).hours(num(hass, hours, 1));
}

////////////////////////////////////////////////////////////////////////////////
// What the integration publishes

/** The hub's decision sensor, the rooms' ones and the unit's own entities. */
function model(hass) {
  const entries = Object.values(hass.entities || {}).filter(
    (entry) => entry.platform === DOMAIN,
  );
  let hub = null;
  const rooms = [];
  const byKey = {};
  for (const entry of entries) {
    const state = hass.states[entry.entity_id];
    if (!state) continue;
    if (entry.translation_key === "decision") {
      if ("mode" in state.attributes) hub = state;
      else {
        const device = (hass.devices || {})[entry.device_id];
        rooms.push({
          id: entry.entity_id,
          state,
          deviceId: entry.device_id,
          name: device?.name_by_user || device?.name || state.attributes.friendly_name,
        });
      }
    } else if (entry.translation_key) {
      byKey[entry.translation_key] = state;
    }
  }
  rooms.sort((a, b) => a.name.localeCompare(b.name));

  // The ventilation integration tags each of its entities with what it is.
  const unit = {};
  for (const state of Object.values(hass.states)) {
    const type = state.attributes?.entity_type;
    if (type && state.attributes.room_number === undefined && !(type in unit)) {
      unit[type] = state;
    }
  }
  return { hub, rooms, own: byKey, unit };
}

function attrs(state) {
  return (state && state.attributes) || {};
}

function thresholdsOf(state) {
  const map = {};
  for (const item of attrs(state).thresholds || []) map[item.key] = item;
  return map;
}

function upcomingOf(state) {
  const map = {};
  for (const item of attrs(state).upcoming || []) map[item.key] = new Date(item.at);
  return map;
}

function source(hass, state, name) {
  const id = (attrs(state).sources || {})[name];
  return id ? hass.states[id] : undefined;
}

function numberOf(state) {
  if (!state) return null;
  const value = Number(state.state);
  return Number.isFinite(value) ? value : null;
}

function setting(state, key) {
  return (attrs(state).settings || {})[key]?.value;
}

function gate(state, name) {
  return (attrs(state).gates || []).find((item) => item.name === name);
}

function roomTemperature(state) {
  return attrs(state).room_temperature ?? null;
}

////////////////////////////////////////////////////////////////////////////////
// History, fetched once and kept for a few minutes

const CACHE = new Map();
const CACHE_TTL = 5 * 60 * 1000;

async function cached(hass, key, fetch) {
  const hit = CACHE.get(key);
  if (hit && Date.now() - hit.at < CACHE_TTL) return hit.promise;
  const promise = fetch().catch(() => null);
  CACHE.set(key, { at: Date.now(), promise });
  return promise;
}

function iso(date) {
  return date.toISOString();
}

function startOfToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

/** State changes per entity, oldest first, as {s, a, t}. */
async function history(hass, entityIds, start, end = new Date(), withAttributes = false) {
  const ids = entityIds.filter(Boolean);
  if (!ids.length || !hass.callWS) return {};
  const key = `h:${ids.join(",")}:${start.getTime()}:${withAttributes}`;
  const raw = await cached(hass, key, () =>
    hass.callWS({
      type: "history/history_during_period",
      start_time: iso(start),
      end_time: iso(end),
      entity_ids: ids,
      minimal_response: !withAttributes,
      no_attributes: !withAttributes,
      significant_changes_only: false,
    }),
  );
  const out = {};
  for (const [id, rows] of Object.entries(raw || {})) {
    let last = {};
    out[id] = rows.map((row) => {
      const item = {
        s: row.s ?? row.state,
        a: row.a ?? row.attributes ?? last.a,
        t: new Date(((row.lu ?? row.lc) || 0) * 1000 || Date.parse(row.last_updated)),
      };
      last = item;
      return item;
    });
  }
  return out;
}

/** Long-term statistics, {id: [{start, mean}]}. */
async function statistics(hass, ids, start, end, period) {
  const list = ids.filter(Boolean);
  if (!list.length || !hass.callWS) return {};
  const key = `s:${list.join(",")}:${start.getTime()}:${end.getTime()}:${period}`;
  const raw = await cached(hass, key, () =>
    hass.callWS({
      type: "recorder/statistics_during_period",
      start_time: iso(start),
      end_time: iso(end),
      statistic_ids: list,
      period,
      types: ["mean"],
    }),
  );
  const out = {};
  for (const [id, rows] of Object.entries(raw || {})) {
    out[id] = rows.map((row) => ({
      start: new Date(typeof row.start === "number" ? row.start : Date.parse(row.start)),
      mean: row.mean,
    }));
  }
  return out;
}

async function logbook(hass, entityIds, start) {
  if (!hass.callWS) return [];
  const key = `l:${entityIds.join(",")}:${start.getTime()}`;
  return (
    (await cached(hass, key, () =>
      hass.callWS({
        type: "logbook/get_events",
        start_time: iso(start),
        end_time: iso(new Date()),
        entity_ids: entityIds,
      }),
    )) || []
  );
}

/** Hours a state held within [start, end), from a history of changes. */
function hoursIn(rows, start, end, matches) {
  let total = 0;
  for (let i = 0; i < rows.length; i += 1) {
    const from = Math.max(rows[i].t.getTime(), start.getTime());
    const to = Math.min(i + 1 < rows.length ? rows[i + 1].t.getTime() : end.getTime(), end.getTime());
    if (to > from && matches(rows[i].s)) total += to - from;
  }
  return total / 3600000;
}

/** Spans a state held, as fractions of [start, end). */
function spans(rows, start, end, matches) {
  const width = end.getTime() - start.getTime();
  const out = [];
  for (let i = 0; i < rows.length; i += 1) {
    if (!matches(rows[i].s)) continue;
    const from = Math.max(rows[i].t.getTime(), start.getTime());
    const to = Math.min(i + 1 < rows.length ? rows[i + 1].t.getTime() : Date.now(), end.getTime());
    if (to > from) out.push([(from - start.getTime()) / width, (to - from) / width]);
  }
  return out;
}

const RUNNING = (state) => !["off", "0", "unknown", "unavailable", "idle", "standby", ""].includes(String(state));

////////////////////////////////////////////////////////////////////////////////
// Look

const STYLE = `
:host {
  --scc-text: var(--primary-text-color, #1b1f24);
  --scc-muted: var(--secondary-text-color, #4f5866);
  --scc-blue: #1a5fc8;
  --scc-orange: #b85500;
  --scc-purple: #7d2aa3;
  --scc-line: var(--divider-color, #e3e7ed);
  --scc-well: color-mix(in srgb, var(--scc-text) 5%, transparent);
  --scc-blue-soft: color-mix(in srgb, var(--scc-blue) 13%, transparent);
  --scc-orange-soft: color-mix(in srgb, var(--scc-orange) 15%, transparent);
  --scc-purple-soft: color-mix(in srgb, var(--scc-purple) 13%, transparent);
  --scc-mono: inherit;
  display: block;
}
:host([dark]) {
  --scc-blue: #7aa8f5;
  --scc-orange: #f2a45f;
  --scc-purple: #d39af0;
}
ha-card { padding: 20px; display: flex; flex-direction: column; gap: 16px; height: 100%; box-sizing: border-box; color: var(--scc-text); container-type: inline-size; }
h2, h3, p, ul, ol { margin: 0; }
ul, ol { padding: 0; list-style: none; }
.eyebrow { font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: .06em; color: var(--scc-muted); }
.title { font-size: 20px; font-weight: 700; line-height: 1.25; }
.lead { font-size: 14px; color: var(--scc-muted); line-height: 1.45; }
.big { font-size: 24px; font-weight: 700; line-height: 1.2; }
.mono { font-variant-numeric: tabular-nums; }
.muted { color: var(--scc-muted); }
.small { font-size: 12px; }
.blue { color: var(--scc-blue); }
.orange { color: var(--scc-orange); }
.row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.split { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: baseline; }
.grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(var(--min, 140px), 1fr)); }
.tile { background: var(--scc-well); border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.tile.blue { background: var(--scc-blue-soft); }
.tile .label { font-size: 12px; color: var(--scc-muted); }
.tile .value { font-size: 18px; font-weight: 700; }
.tile .note { font-size: 12px; color: var(--scc-muted); }
.note-box { background: var(--scc-well); border-radius: 10px; padding: 10px 12px; font-size: 13px; line-height: 1.45; color: var(--scc-muted); }
.pill { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 500; white-space: nowrap; }
.pill.blue { color: var(--scc-blue); background: var(--scc-blue-soft); }
.pill.orange { color: var(--scc-orange); background: var(--scc-orange-soft); }
.pill.grey { color: var(--scc-text); background: var(--scc-well); }
.pill.solid { color: #fff; background: var(--scc-orange); }
.pill.purple { color: var(--scc-purple); background: var(--scc-purple-soft); }
.dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.dot.blue { background: var(--scc-blue); }
.dot.orange { background: var(--scc-orange); }
.dot.grey { background: var(--scc-muted); }
.dot.purple { background: var(--scc-purple); }
.pulse { box-shadow: 0 0 0 4px var(--scc-orange-soft); }
.checks { display: flex; flex-direction: column; gap: 8px; }
.check { display: grid; grid-template-columns: 20px minmax(0, 1fr); gap: 8px; font-size: 14px; line-height: 1.4; }
.check .mark { font-weight: 700; }
.lever { display: flex; flex-direction: column; gap: 6px; }
.track { position: relative; height: 8px; border-radius: 4px; background: var(--scc-well); overflow: hidden; }
.track > span { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px; background: color-mix(in srgb, var(--scc-blue) 45%, transparent); }
.track.near > span { background: var(--scc-orange); }
.causes > li { display: grid; grid-template-columns: 84px minmax(0, 1fr); gap: 12px; padding: 12px 0; border-top: 1px solid var(--scc-line); }
.causes > li:first-child { border-top: 0; padding-top: 0; }
.causes .q { font-size: 15px; font-weight: 500; }
.causes .a { font-size: 14px; line-height: 1.45; color: var(--scc-muted); }
.causes .pill { justify-self: start; align-self: start; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: .05em; color: var(--scc-muted); padding: 0 10px 10px; }
td, tbody th { padding: 14px 10px; border-top: 1px solid var(--scc-line); vertical-align: top; text-transform: none; letter-spacing: 0; }
tbody th { font-size: 14px; font-weight: 500; color: var(--scc-text); }
.scroll { overflow-x: auto; margin: 0 -10px; }
/* On a narrow card the room table turns into one block per room. */
@container (max-width: 640px) {
  .stack thead { display: none; }
  .stack, .stack tbody { display: block; }
  .stack tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px 12px; padding: 14px 10px; border-top: 1px solid var(--scc-line); }
  .stack tr:first-child { border-top: 0; }
  .stack td, .stack tbody th { display: block; padding: 0; border: 0; }
  .stack td:nth-of-type(1) { text-align: right; }
  .stack td:nth-of-type(n+2) { grid-column: 1 / -1; }
  .stack td:nth-of-type(2) { display: none; }
  .stack .narrow-only { display: inline-flex; }
}
.narrow-only { display: none; }
a { color: var(--scc-blue); }
a.nav { text-decoration: none; font-weight: 500; }
a.nav:hover { text-decoration: underline; }
.links { display: flex; flex-wrap: wrap; gap: 8px; }
.links a { display: inline-flex; align-items: center; min-height: 40px; padding: 0 14px; border-radius: 999px; background: var(--scc-well); color: var(--scc-text); text-decoration: none; font-size: 14px; font-weight: 500; }
.links a:hover { background: var(--scc-blue-soft); color: var(--scc-blue); }
.steps > li { display: grid; grid-template-columns: 26px minmax(0, 1fr); gap: 10px; }
.steps .rail { display: flex; flex-direction: column; align-items: center; }
.steps .node { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.steps .node.done { background: var(--scc-blue); color: #fff; }
.steps .node.now { background: var(--scc-orange); color: #fff; }
.steps .node.todo { background: var(--scc-well); color: var(--scc-muted); }
.steps .line { flex: 1; width: 2px; min-height: 16px; background: var(--scc-line); }
.steps .line.done { background: var(--scc-blue); }
.steps .body { display: flex; flex-direction: column; gap: 2px; padding-bottom: 14px; }
.steps li:last-child .line { display: none; }
.events > li { display: grid; grid-template-columns: 92px 14px minmax(0, 1fr); gap: 12px; padding: 12px 0; border-top: 1px solid var(--scc-line); }
.events > li:first-child { border-top: 0; }
.events .dot { margin-top: 4px; }
.bars { display: flex; align-items: flex-end; gap: 4px; height: 72px; }
.bars > span { flex: 1; min-width: 0; border-radius: 3px 3px 0 0; background: var(--scc-blue); }
.bars > span.today { background: color-mix(in srgb, var(--scc-blue) 45%, transparent); }
.timeline { position: relative; height: 44px; }
.timeline .band { position: absolute; top: 0; height: 18px; border-radius: 4px; }
.timeline .night { background: color-mix(in srgb, var(--scc-text) 12%, transparent); }
.timeline .run { position: absolute; top: 3px; height: 12px; border-radius: 2px; background: var(--scc-orange); }
.timeline .fan { position: absolute; top: 21px; height: 4px; border-radius: 2px; background: color-mix(in srgb, var(--scc-blue) 60%, transparent); }
.timeline .now { position: absolute; top: -3px; width: 2px; height: 28px; background: var(--scc-text); }
.timeline .ticks { position: absolute; left: 0; right: 0; top: 30px; display: flex; justify-content: space-between; font-size: 11px; color: var(--scc-muted); font-variant-numeric: tabular-nums; }
.path { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.stage { display: flex; flex-direction: column; gap: 2px; padding: 10px 14px; border-radius: 12px; min-width: 104px; background: var(--scc-well); }
.stage.cold { background: var(--scc-blue-soft); }
.stage.warm { background: var(--scc-orange-soft); }
.stage.hot { background: color-mix(in srgb, var(--scc-orange) 28%, transparent); }
.stage .t { font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }
.arrow { color: var(--scc-muted); }
.week { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 8px; align-items: end; }
.week .col { display: flex; flex-direction: column; gap: 6px; text-align: center; font-size: 12px; }
.week .well { height: 80px; display: flex; align-items: flex-end; justify-content: center; background: var(--scc-well); border-radius: 6px; overflow: hidden; }
.week .well > span { width: 46%; background: var(--scc-orange); min-height: 2px; border-radius: 3px 3px 0 0; }
.hero { display: flex; gap: 14px; align-items: flex-start; }
.badge { flex: none; width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.badge.orange { background: var(--scc-orange-soft); color: var(--scc-orange); }
.badge.blue { background: var(--scc-blue-soft); color: var(--scc-blue); }
.figures { display: flex; gap: 24px; flex-wrap: wrap; }
.figure { display: flex; flex-direction: column; }
.figure .v { font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
.statement { font-size: 17px; line-height: 1.5; }
svg text { fill: var(--scc-muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.empty { color: var(--scc-muted); font-size: 14px; }
`;

const ICONS = {
  trendDown: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7l6 6 4-4 8 8"></path><path d="M14 17h7v-7"></path></svg>',
  trendUp: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8"></path><path d="M14 7h7v7"></path></svg>',
  check: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"></path></svg>',
  alert: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z"></path><path d="M12 10v5"></path><path d="M12 18h.01"></path></svg>',
  arrow: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path></svg>',
  back: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"></path></svg>',
};

////////////////////////////////////////////////////////////////////////////////
// Building blocks

function pill(text, tone) {
  return `<span class="pill ${tone}">${esc(text)}</span>`;
}

function tile(label, value, note = "", tone = "") {
  return `<div class="tile"><span class="label">${esc(label)}</span><span class="value ${tone}">${esc(value)}</span>${note ? `<span class="note">${esc(note)}</span>` : ""}</div>`;
}

function check(ok, text) {
  return `<li class="check"><span class="mark ${ok ? "blue" : "orange"}">${ok ? "✓" : "–"}</span><span>${esc(text)}</span></li>`;
}

function cause(hass, kind, question, answer) {
  const w = words(hass);
  const look = { yes: ["orange", w.tagYes], part: ["purple", w.tagPart], no: ["blue", w.tagNo], wait: ["purple", w.tagWaits], unknown: ["grey", w.tagUnknown] }[kind];
  return `<li>${pill(look[1], look[0])}<div><div class="q">${esc(question)}</div><div class="a">${esc(answer)}</div></div></li>`;
}

/** One lever: what would change, how far off, and a bar that fills as it nears. */
function lever(title, right, rule, closeness, near) {
  const fill = Math.round(Math.min(1, Math.max(0.03, closeness)) * 100);
  return `<div class="lever"><div class="split" style="font-size:14px"><span style="font-weight:500">${esc(title)}</span><span class="mono ${near ? "orange" : ""}" style="font-weight:500">${esc(right)}</span></div><div class="track ${near ? "near" : ""}"><span style="width:${fill}%"></span></div><span class="small muted">${esc(rule)}</span></div>`;
}

/** How full a threshold's bar is: the nearer the limit, the fuller. A room's
 * rules work in tenths of a kelvin, the outdoor ones in whole kelvin. */
const SCALE = { "°C": 10, K: 3, W: 1500 };
const ROOM_SCALE = 3;
/** Close enough to colour: a change this near is worth a glance. */
const NEAR = { "°C": 0.3, K: 0.3, W: 100 };

function thresholdLever(hass, item) {
  const w = words(hass);
  const [title, rule] = OUTLOOK[lang(hass)][item.key] || [item.key, () => ""];
  const unit = item.unit;
  const shown = {
    value: withUnit(hass, item.value, unit),
    limit: withUnit(hass, item.limit, unit),
  };
  const distance = item.distance;
  const scale = /^(aux_|frost)/.test(item.key) && unit !== "W" ? ROOM_SCALE : SCALE[unit] || 10;
  const closeness = distance === null ? 0 : 1 - Math.min(1, Math.max(0, distance) / scale);
  const near = distance !== null && distance > 0 && distance <= (NEAR[unit] ?? 0);
  const right = distance === null ? "–" : distance <= 0 ? w.passed : withUnit(hass, distance, unit === "°C" ? "K" : unit);
  return { html: lever(title, right, rule(shown), closeness, near), closeness };
}

function eventLever(hass, key, at) {
  const w = words(hass);
  const [title, rule] = OUTLOOK[lang(hass)][key] || [key, () => ""];
  const ms = at.getTime() - Date.now();
  const closeness = 1 - Math.min(1, Math.max(0, ms) / (12 * 3600000));
  return {
    html: lever(title, `${w.inTime(duration(hass, ms))}`, `${w.atTime(clock(hass, at))} · ${rule()}`, closeness, ms < 30 * 60000),
    closeness,
  };
}

function navigate(path) {
  window.history.pushState(null, "", path);
  window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
}

/** A path inside the dashboard the card sits in. */
function viewPath(view) {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return `/${parts[0] || "lovelace"}/${view}`;
}

function slug(text) {
  return String(text)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replaceAll("ß", "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function roomView(room) {
  return `raum-${slug(room.name)}`;
}

////////////////////////////////////////////////////////////////////////////////
// The base every card shares

class SccCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
  }

  set hass(hass) {
    this._hass = hass;
    if (hass.themes?.darkMode) this.setAttribute("dark", "");
    else this.removeAttribute("dark");
    const watched = this.watched(hass).map((id) => hass.states[id]);
    const changed = !this._watched || watched.length !== this._watched.length || watched.some((s, i) => s !== this._watched[i]);
    if (changed) {
      this._watched = watched;
      this._render();
      this._load();
    }
  }

  get hass() {
    return this._hass;
  }

  /** Entities whose change re-renders the card. */
  watched(hass) {
    const m = model(hass);
    return [m.hub?.entity_id, ...m.rooms.map((room) => room.id)].filter(Boolean);
  }

  /** History the card wants, fetched after a render; null when none. */
  async fetch() {
    return null;
  }

  async _load() {
    const token = (this._token = (this._token || 0) + 1);
    const data = await this.fetch(this._hass);
    if (data !== null && token === this._token) {
      this._data = data;
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const body = this.content(this._hass, model(this._hass));
    if (body === null) {
      this.shadowRoot.innerHTML = "";
      this.style.display = "none";
      return;
    }
    this.style.display = "";
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card>${body}</ha-card>`;
    this.shadowRoot.querySelectorAll("a[data-view]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigate(viewPath(link.dataset.view));
      });
    });
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, rows: "auto" };
  }
}

function link(view, text) {
  return `<a class="nav" href="${esc(viewPath(view))}" data-view="${esc(view)}">${text}</a>`;
}

////////////////////////////////////////////////////////////////////////////////
// Sentences built from the decisions

const SENTENCES = {
  de: {
    reason: {
      heat_released: (v) => `Freigegeben, weil es draußen ${v.outdoor} hat, unter ${v.limit}`,
      heat_too_warm: (v) => `Nicht freigegeben: draußen ${v.outdoor}, Heizen erst unter ${v.limit}`,
      forecast_warm: (v) => `Nicht freigegeben: die Prognose sagt ${v.forecast}, das reicht ohne Wärmepumpe`,
      release_locked: () => "Gehalten: Die Freigabe wechselt erst nach der Sperrzeit",
      frost_protection: () => "Freigegeben wegen Frostschutz: ein Raum ist zu kalt",
      cool_released: (v) => `Kühlen freigegeben: der wärmste Raum liegt über ${v.coolLimit} und es gibt Überschuss`,
      cool_not_needed: (v) => `Kühlen nicht nötig: kein Raum über ${v.coolLimit}`,
      cool_no_surplus: () => "Kühlen wartet auf PV-Überschuss",
      ventilation_only: () => "Nur Lüften: weder Heizen noch Kühlen erlaubt",
      outdoor_unavailable: () => "Nur Lüften: die Außentemperatur fehlt",
      controller_disabled: () => "Der Controller ist aus",
    },
    forecastOff: (v) => `Prognose zählt erst ab ${v.floor} draußen, heute ${v.forecast} Höchstwert`,
    forecastOn: (v) => `Prognose: Höchstwert ${v.forecast}, sperrt ab ${v.limit}`,
    fan: {
      fixed_stage: (v) => `Luftstufe ${v.level}, fest eingestellt`,
      boost: (v) => `Luftstufe ${v.level}, Stoßlüften`,
      co2_high: (v) => `Luftstufe ${v.level}, CO₂ hoch${v.room ? ` in ${v.room}` : ""}`,
      humidity_high: (v) => `Luftstufe ${v.level}, Feuchte hoch${v.room ? ` in ${v.room}` : ""}`,
      night_cooling: (v) => `Luftstufe ${v.level}, Nachtauskühlung`,
      heat_pump: (v) => `Luftstufe ${v.level}, angehoben weil die Wärmepumpe läuft`,
      heat_protection: (v) => `Luftstufe ${v.level}, gedrosselt: draußen ist es wärmer`,
      holiday: (v) => `Luftstufe ${v.level}, Urlaub`,
      night: (v) => `Luftstufe ${v.level}, Nacht`,
      normal: (v) => `Luftstufe ${v.level}`,
    },
    temps: (v) => `Zuluft ${v.supply}${v.condenser ? `, Kondensator ${v.condenser}` : ""}`,
    auxRunning: "Läuft",
    auxRunningWhy: {
      override: (v) => `${v.deficit} unter Soll, die Zuluft zählt da nicht mehr`,
      supply: (v) => `Die Zuluft ist nur ${v.lift} wärmer als der Raum`,
      stalled: () => "Mit der Zuluft allein holt der Raum nicht auf",
      plain: (v) => `${v.deficit} unter Soll`,
    },
    auxWaiting: (v) => `Wartet noch ${v.left}, dann an`,
    auxWatching: (v) => `Zuluft ${v.lift} wärmer als der Raum, die Wärmepumpe soll es schaffen. Raum wird beobachtet: ${v.rise} von ${v.need} gestiegen.`,
    auxSmall: (v) => `Nur ${v.deficit} unter Soll, der Zuheizer kommt ab ${v.start}.`,
    auxAbove: "Auf oder über Soll.",
    auxLocked: {
      mode: "Kein Heizmodus.",
      release: "Die Wärmepumpe ist nicht freigegeben.",
      outdoor: (v) => `Draußen ${v.outdoor}, Zuheizer erst unter ${v.limit}.`,
      window: "Fenster offen.",
      night: "Nachts in diesem Raum aus.",
      temperature: "Keine Raumtemperatur.",
    },
    ownHeater: "eigene Heizung",
    ownHeaterOn: "darf heizen",
    ownHeaterOff: "darf nicht heizen",
  },
  en: {
    reason: {
      heat_released: (v) => `Released, because it is ${v.outdoor} outdoors, below ${v.limit}`,
      heat_too_warm: (v) => `Not released: ${v.outdoor} outdoors, heating only below ${v.limit}`,
      forecast_warm: (v) => `Not released: the forecast says ${v.forecast}, enough without the heat pump`,
      release_locked: () => "Held: the release changes only after the lockout",
      frost_protection: () => "Released for frost protection: a room is too cold",
      cool_released: (v) => `Cooling released: the warmest room is above ${v.coolLimit} and there is surplus`,
      cool_not_needed: (v) => `No cooling needed: no room above ${v.coolLimit}`,
      cool_no_surplus: () => "Cooling waits for PV surplus",
      ventilation_only: () => "Ventilation only: neither heating nor cooling allowed",
      outdoor_unavailable: () => "Ventilation only: the outdoor temperature is missing",
      controller_disabled: () => "The controller is off",
    },
    forecastOff: (v) => `The forecast only counts from ${v.floor} outdoors, today's high ${v.forecast}`,
    forecastOn: (v) => `Forecast: high ${v.forecast}, blocks from ${v.limit}`,
    fan: {
      fixed_stage: (v) => `Fan level ${v.level}, fixed`,
      boost: (v) => `Fan level ${v.level}, boost`,
      co2_high: (v) => `Fan level ${v.level}, CO₂ high${v.room ? ` in ${v.room}` : ""}`,
      humidity_high: (v) => `Fan level ${v.level}, humidity high${v.room ? ` in ${v.room}` : ""}`,
      night_cooling: (v) => `Fan level ${v.level}, night cooling`,
      heat_pump: (v) => `Fan level ${v.level}, raised because the heat pump runs`,
      heat_protection: (v) => `Fan level ${v.level}, capped: it is warmer outdoors`,
      holiday: (v) => `Fan level ${v.level}, holiday`,
      night: (v) => `Fan level ${v.level}, night`,
      normal: (v) => `Fan level ${v.level}`,
    },
    temps: (v) => `Supply air ${v.supply}${v.condenser ? `, condenser ${v.condenser}` : ""}`,
    auxRunning: "Running",
    auxRunningWhy: {
      override: (v) => `${v.deficit} below target, the supply air no longer counts`,
      supply: (v) => `The supply air is only ${v.lift} above the room`,
      stalled: () => "The room does not catch up on supply air alone",
      plain: (v) => `${v.deficit} below target`,
    },
    auxWaiting: (v) => `Waiting another ${v.left}, then on`,
    auxWatching: (v) => `Supply air ${v.lift} above the room, the heat pump should manage. Watching the room: risen ${v.rise} of ${v.need}.`,
    auxSmall: (v) => `Only ${v.deficit} below target, the heater comes from ${v.start}.`,
    auxAbove: "At or above target.",
    auxLocked: {
      mode: "Not heating.",
      release: "The heat pump is not released.",
      outdoor: (v) => `${v.outdoor} outdoors, aux heaters only below ${v.limit}.`,
      window: "Window open.",
      night: "Off at night in this room.",
      temperature: "No room temperature.",
    },
    ownHeater: "own heater",
    ownHeaterOn: "may heat",
    ownHeaterOff: "may not heat",
  },
};

function say(hass) {
  return SENTENCES[lang(hass)];
}

function deg(hass, value) {
  return withUnit(hass, value, "°C");
}

function kelvin(hass, value) {
  return withUnit(hass, value, "K");
}

/** The levers of one decision, nearest first. */
function levers(hass, state, keys, limit = 4) {
  const thr = thresholdsOf(state);
  const up = upcomingOf(state);
  const out = [];
  for (const key of keys) {
    if (thr[key]) out.push(thresholdLever(hass, thr[key]));
    if (up[key] && up[key].getTime() > Date.now()) out.push(eventLever(hass, key, up[key]));
  }
  return out.sort((a, b) => b.closeness - a.closeness).slice(0, limit);
}

/** What a WGT room's heater is doing, and why, in a word and a sentence. */
function auxStatus(hass, hub, room) {
  const w = words(hass);
  const s = say(hass);
  const a = attrs(room.state);
  const thr = thresholdsOf(room.state);
  const temperature = roomTemperature(room.state);
  const target = a.target_temperature;
  if (a.auxiliary_heat === null || a.auxiliary_heat === undefined) {
    return {
      wgt: false,
      allowed: a.heating_enabled === true,
      state: a.heating_enabled ? s.ownHeaterOn : s.ownHeaterOff,
      tone: a.heating_enabled ? "blue" : "grey",
      why: s.ownHeater,
    };
  }
  const outdoorGate = gate(room.state, "aux_outdoor_cold");
  const nightGate = gate(room.state, "aux_allowed_now");
  const hubAttrs = attrs(hub);
  let locked = null;
  if (hubAttrs.mode !== "heating") locked = s.auxLocked.mode;
  else if (!hubAttrs.heat_release) locked = s.auxLocked.release;
  else if (outdoorGate && !outdoorGate.passed && thr.aux_outdoor)
    locked = s.auxLocked.outdoor({ outdoor: deg(hass, thr.aux_outdoor.value), limit: deg(hass, thr.aux_outdoor.limit) });
  else if (a.window_open) locked = s.auxLocked.window;
  else if (nightGate && !nightGate.passed) locked = s.auxLocked.night;
  else if (temperature === null) locked = s.auxLocked.temperature;

  const deficit = target !== null && temperature !== null ? target - temperature : null;
  if (a.auxiliary_heat) {
    let why = s.auxRunningWhy.plain({ deficit: kelvin(hass, deficit) });
    if (gate(room.state, "aux_override")?.passed) why = s.auxRunningWhy.override({ deficit: kelvin(hass, deficit) });
    else if (gate(room.state, "aux_not_catching_up")?.passed) why = s.auxRunningWhy.stalled();
    else if (gate(room.state, "aux_supply_insufficient")?.passed && thr.aux_supply) why = s.auxRunningWhy.supply({ lift: kelvin(hass, thr.aux_supply.value) });
    return { wgt: true, allowed: true, state: w.on, tone: "solid", why };
  }
  if (locked) return { wgt: true, allowed: false, state: w.off, tone: "grey", why: locked };
  if (a.auxiliary_heat_waiting_since) {
    const on = upcomingOf(room.state).aux_on;
    const left = on ? duration(hass, on.getTime() - Date.now()) : "";
    return { wgt: true, allowed: true, state: w.tagWaits, tone: "purple", why: s.auxWaiting({ left }) };
  }
  if (thr.aux_rise) {
    return {
      wgt: true,
      allowed: true,
      state: w.off,
      tone: "grey",
      why: s.auxWatching({
        lift: kelvin(hass, thr.aux_supply?.value ?? null),
        rise: kelvin(hass, thr.aux_rise.value),
        need: kelvin(hass, thr.aux_rise.limit),
      }),
    };
  }
  const start = setting(room.state, "aux_deficit") ?? 0.5;
  if (deficit !== null && deficit > 0.05) {
    return { wgt: true, allowed: true, state: w.off, tone: "grey", why: s.auxSmall({ deficit: kelvin(hass, deficit), start: kelvin(hass, start) }) };
  }
  return { wgt: true, allowed: true, state: w.off, tone: "grey", why: s.auxAbove };
}

function deltaText(hass, room) {
  const w = words(hass);
  const a = attrs(room.state);
  const temperature = roomTemperature(room.state);
  if (temperature === null || a.target_temperature === null || a.target_temperature === undefined) return ["", ""];
  const delta = temperature - a.target_temperature;
  if (Math.abs(delta) < 0.05) return [w.atTarget, ""];
  return delta < 0 ? [w.tooCold(kelvin(hass, -delta)), delta <= -0.5 ? "orange" : ""] : [w.tooWarm(kelvin(hass, delta)), ""];
}

const ROOM_LEVERS = ["aux_on", "aux_verdict", "aux_wanted", "aux_override", "aux_supply", "aux_rise", "aux_reached", "aux_outdoor", "frost_protection", "night_starts", "night_ends"];

////////////////////////////////////////////////////////////////////////////////
// Needs attention: only there when something does

class AlertsCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    return [...super.watched(hass), m.own.missing_inputs?.entity_id, m.own.dry_run?.entity_id, m.own.active?.entity_id, m.unit.error_message?.entity_id].filter(Boolean);
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const a = attrs(m.hub);
    const items = [];
    if (m.hub.state === "disabled") items.push(w.alertDisabled);
    if (m.own.dry_run?.state === "on") items.push(w.alertDryRun);
    if ((a.failed_inputs || []).length) items.push(w.alertMissing(a.failed_inputs.join(", ")));
    const stuck = attrs(m.own.missing_inputs).stuck_writes || [];
    if (stuck.length) items.push(w.alertStuck(stuck.join(", ")));
    const operation = source(hass, m.hub, "operation_mode");
    if (operation && !["manual", "unknown", "unavailable"].includes(operation.state)) items.push(w.alertManual(operation.state));
    const fault = m.unit.error_message;
    if (fault && !["0", "unknown", "unavailable", ""].includes(fault.state)) items.push(w.alertFault(fault.state));
    if (gate(m.hub, "frost_protection")?.passed === false) items.push(w.alertFrost);
    if (!items.length) return null;
    return `<div class="hero"><span class="badge orange">${ICONS.alert}</span><div style="display:flex;flex-direction:column;gap:6px"><span class="title">${esc(w.alerts)}</span><ul class="checks">${items.map((text) => `<li class="lead">${esc(text)}</li>`).join("")}</ul></div></div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Is the system doing well?

class HealthCard extends SccCard {
  async fetch(hass) {
    const m = model(hass);
    if (!m.hub) return null;
    const extract = (attrs(m.hub).sources || {}).extract;
    const compressor = (attrs(m.hub).sources || {}).compressor;
    const end = new Date();
    const start = new Date(end.getTime() - 8 * 86400000);
    const [stats, runs] = await Promise.all([
      statistics(hass, [extract], start, end, "day"),
      history(hass, [compressor], startOfToday()),
    ]);
    return { extract: (stats || {})[extract] || [], compressor: (runs || {})[compressor] || [] };
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const a = attrs(m.hub);
    const mode = a.mode;
    const rooms = m.rooms.filter((room) => roomTemperature(room.state) !== null && attrs(room.state).target_temperature != null);
    const deficits = rooms.map((room) => ({ room, d: attrs(room.state).target_temperature - roomTemperature(room.state) }));
    const below = deficits.filter((x) => x.d >= 0.5).sort((x, y) => y.d - x.d);
    const above = deficits.filter((x) => x.d <= -0.5).sort((x, y) => x.d - y.d);

    const series = (this._data?.extract || []).filter((row) => row.mean !== null && row.mean !== undefined);
    const trend = series.length >= 2 ? series[series.length - 1].mean - series[0].mean : null;
    const trendSince = series.length >= 2 ? dayLabel(hass, series[0].start) : "";
    const extractNow = numberOf(source(hass, m.hub, "extract"));
    const runs = this._data?.compressor || [];
    const today = runs.length ? hoursIn(runs, startOfToday(), new Date(), RUNNING) : null;

    let verdict;
    let lead;
    let tone;
    let icon;
    if (mode === "cooling") {
      const warm = above.length;
      [verdict, lead, tone, icon] = warm ? [w.verdictWarm, w.leadWarm, "orange", ICONS.trendUp] : [w.verdictCool, w.leadCool, "blue", ICONS.check];
    } else if (mode === "ventilation") {
      const bad = m.rooms.filter((room) => (attrs(room.state).gates || []).some((g) => (g.name === "co2_high" || g.name === "humidity_high") && g.passed));
      [verdict, lead, tone, icon] = bad.length ? [w.verdictAirBad, w.leadAirBad, "orange", ICONS.alert] : [w.verdictAir, w.leadAir, "blue", ICONS.check];
    } else if (trend !== null && trend <= -0.5) {
      [verdict, lead, tone, icon] = [w.verdictBehind, w.leadBehind(kelvin(hass, -trend), trendSince), "orange", ICONS.trendDown];
    } else if (below.length && trend !== null && trend > 0.1) {
      [verdict, lead, tone, icon] = [w.verdictCatching, w.leadCatching, "blue", ICONS.trendUp];
    } else if (below.length) {
      [verdict, lead, tone, icon] = [w.verdictBehind, w.leadBehindRooms, "orange", ICONS.trendDown];
    } else {
      [verdict, lead, tone, icon] = [w.verdictGood, w.leadGood, "blue", ICONS.check];
    }

    const tiles = [];
    if (mode === "cooling") {
      tiles.push(tile(w.roomsAbove, `${above.length} / ${rooms.length}`, above[0] ? `${above[0].room.name} ${kelvin(hass, -above[0].d)}` : "", above.length ? "orange" : ""));
    } else {
      tiles.push(tile(w.roomsBelow, `${below.length} / ${rooms.length}`, below[0] ? `${below[0].room.name} ${kelvin(hass, below[0].d)}` : "", below.length ? "orange" : ""));
    }
    tiles.push(tile(w.houseExtract, deg(hass, extractNow), trend !== null ? w.sinceDays(`${trend >= 0 ? "+" : "−"}${kelvin(hass, Math.abs(trend))}`, trendSince) : "", trend !== null && trend <= -0.5 ? "orange" : ""));
    if (mode === "heating") tiles.push(tile(w.hpToday, today === null ? "–" : hoursText(hass, today), w.today));

    return `<span class="eyebrow">${esc(w.health)}</span>
      <div class="hero"><span class="badge ${tone}">${icon}</span><div style="display:flex;flex-direction:column;gap:4px"><span class="big ${tone}">${esc(verdict)}</span><span class="lead">${esc(lead)}</span></div></div>
      <div class="grid" style="--min:118px">${tiles.join("")}</div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Energy

class EnergyCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    const power = (attrs(m.hub).sources || {}).power;
    return [m.hub?.entity_id, power].filter(Boolean);
  }

  async fetch(hass) {
    const m = model(hass);
    const sources = attrs(m.hub).sources || {};
    if (!sources.power) return null;
    const now = new Date();
    const today = startOfToday();
    const fortnight = new Date(today.getTime() - 13 * 86400000);
    const yearAgo = new Date(today.getTime() - 365 * 86400000);
    const [hours, days, lastYear] = await Promise.all([
      statistics(hass, [sources.power], today, now, "hour"),
      statistics(hass, [sources.power, sources.extract, sources.outdoor], fortnight, now, "day"),
      statistics(hass, [sources.power], new Date(yearAgo.getTime() - 6 * 86400000), new Date(yearAgo.getTime() + 86400000), "day"),
    ]);
    return { hours: (hours || {})[sources.power] || [], days: days || {}, lastYear: (lastYear || {})[sources.power] || [], sources };
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const power = source(hass, m.hub, "power");
    if (!power) {
      return `<span class="eyebrow">${esc(w.energy)}</span><p class="empty">${esc(w.noPower)}</p>`;
    }
    const data = this._data;
    const kwh = (rows, hoursEach) => rows.reduce((sum, row) => sum + (row.mean || 0) * hoursEach, 0) / 1000;
    const today = data ? kwh(data.hours, 1) : null;
    const dayRows = data ? data.days[data.sources.power] || [] : [];
    const perDay = dayRows.map((row) => ({ start: row.start, kwh: (row.mean || 0) * 24 / 1000 }));
    if (perDay.length && today !== null) perDay[perDay.length - 1].kwh = today;
    const week = perDay.slice(-7).reduce((sum, row) => sum + row.kwh, 0);
    const lastYear = data && data.lastYear.length ? kwh(data.lastYear, 24) : null;

    // Per kelvin between inside and out, so a cold week and a mild one compare.
    let normalised = null;
    if (data) {
      const extract = data.days[data.sources.extract] || [];
      const outdoor = data.days[data.sources.outdoor] || [];
      const pairs = perDay.slice(-8, -1).map((row) => {
        const e = extract.find((x) => x.start.getTime() === row.start.getTime());
        const o = outdoor.find((x) => x.start.getTime() === row.start.getTime());
        return e && o && e.mean - o.mean > 2 ? row.kwh / (e.mean - o.mean) : null;
      }).filter((x) => x !== null);
      if (pairs.length) normalised = pairs.reduce((s, x) => s + x, 0) / pairs.length;
    }

    const max = Math.max(0.5, ...perDay.map((row) => row.kwh));
    const bars = perDay.map((row, i) => `<span class="${i === perDay.length - 1 ? "today" : ""}" style="height:${Math.max(2, Math.round((row.kwh / max) * 100))}%" title="${esc(dayLabel(hass, row.start))}: ${esc(withUnit(hass, row.kwh, "kWh"))}"></span>`).join("");
    const first = perDay[0];
    const middle = perDay[Math.floor(perDay.length / 2)];
    const last = perDay[perDay.length - 1];

    return `<span class="eyebrow">${esc(w.energy)}</span>
      <div class="grid" style="--min:110px">
        ${tile(w.energyNow, withUnit(hass, numberOf(power), "W"))}
        ${tile(w.energyToday, today === null ? w.loading : withUnit(hass, today, "kWh"))}
        ${tile(w.energyWeek, data ? withUnit(hass, week, "kWh") : w.loading, data ? w.perDay(withUnit(hass, week / Math.max(1, Math.min(7, perDay.length)), "kWh")) : "")}
        ${tile(w.energyLastYear, lastYear === null ? "–" : withUnit(hass, lastYear, "kWh"), lastYear === null ? w.noData : w.lastYearSame(""))}
      </div>
      ${perDay.length ? `<div style="display:flex;flex-direction:column;gap:6px">
        <div class="split small muted"><span>${esc(w.daysChart)}</span>${normalised !== null ? `<span>${esc(w.normalised(num(hass, normalised, 2)))}</span>` : ""}</div>
        <div class="bars" role="img" aria-label="${esc(w.daysChart)}">${bars}</div>
        <div class="split small muted mono"><span>${esc(dayLabel(hass, first.start))}</span><span>${esc(dayLabel(hass, middle.start))}</span><span>${esc(dayLabel(hass, last.start))}</span></div>
      </div>` : ""}`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Heat pump

class HeatPumpCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    const s = attrs(m.hub).sources || {};
    return [m.hub?.entity_id, s.compressor, s.heat_release, s.cool_release, s.function, s.supply_air, m.unit.temperature_t8_condenser?.entity_id].filter(Boolean);
  }

  async fetch(hass) {
    const m = model(hass);
    const s = attrs(m.hub).sources || {};
    const fan = m.unit.current_fan_level?.entity_id || s.fan;
    const rows = await history(hass, [s.compressor, fan], startOfToday());
    return { compressor: (rows || {})[s.compressor] || [], fan: (rows || {})[fan] || [] };
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const s = say(hass);
    const a = attrs(m.hub);
    const thr = thresholdsOf(m.hub);
    const heatSwitch = source(hass, m.hub, "heat_release");
    const coolSwitch = source(hass, m.hub, "cool_release");
    const fn = source(hass, m.hub, "function");
    const compressor = source(hass, m.hub, "compressor");
    const heatOn = heatSwitch ? heatSwitch.state === "on" : !!a.heat_release;
    const coolOn = coolSwitch ? coolSwitch.state === "on" : !!a.cool_release;
    const releasedFor = heatOn ? [w.heat, "blue"] : coolOn ? [w.cool, "blue"] : [w.nothing, "muted"];
    const releasedSince = heatOn ? heatSwitch : coolOn ? coolSwitch : heatSwitch;

    const box = (label, value, active) => `<div class="tile ${active ? "blue" : ""}"><span class="label">${esc(label)}</span><span class="value ${active ? "blue" : "muted"}" style="font-size:15px">${esc(value)}</span></div>`;

    // What it does.
    const running = compressor && RUNNING(compressor.state);
    const doing = running ? (coolOn ? w.cooling : w.heating) : w.idle;
    const runs = this._data?.compressor || [];
    const today = runs.length ? hoursIn(runs, startOfToday(), new Date(), RUNNING) : null;
    const meta = [compressor ? w.since(sinceText(hass, new Date(compressor.last_changed))) : "", today !== null ? w.todayHours(hoursText(hass, today)) : ""].filter(Boolean).join(" · ");

    const outdoor = a.outdoor_temperature;
    const why = [];
    const reason = s.reason[a.reason_code];
    if (reason) {
      why.push([a.reason_code !== "heat_too_warm" && a.reason_code !== "release_locked", reason({
        outdoor: deg(hass, outdoor),
        limit: deg(hass, setting(m.hub, "heat_release_below")),
        forecast: deg(hass, thr.forecast_blocks?.value),
        coolLimit: deg(hass, setting(m.hub, "cool_release_above")),
      })]);
    }
    if (thr.forecast_blocks && a.mode === "heating") {
      const counts = thr.forecast_counts && thr.forecast_counts.distance <= 0;
      why.push([true, counts
        ? s.forecastOn({ forecast: deg(hass, thr.forecast_blocks.value), limit: deg(hass, thr.forecast_blocks.limit) })
        : s.forecastOff({ floor: deg(hass, thr.forecast_counts?.limit), forecast: deg(hass, thr.forecast_blocks.value) })]);
    }
    if (a.fan_level !== null && a.fan_level !== undefined) {
      const room = m.rooms.find((r) => r.id === a.fan_requested_by || r.state.attributes.friendly_name === a.fan_requested_by);
      why.push([true, (s.fan[a.fan_reason] || s.fan.normal)({ level: a.fan_level, room: room?.name || a.fan_requested_by })]);
    }
    const supply = numberOf(source(hass, m.hub, "supply_air"));
    if (supply !== null) why.push([true, s.temps({ supply: deg(hass, supply), condenser: m.unit.temperature_t8_condenser ? deg(hass, numberOf(m.unit.temperature_t8_condenser)) : "" })]);
    const hint = heatOn && !running && a.is_night && Number(a.fan_level) < 2 ? ` ${w.stageOneObserved}` : "";

    const leverHtml = levers(hass, m.hub, ["heat_release_off", "heat_release_on", "forecast_blocks", "cool_release_on", "cool_release_off", "surplus_on", "fan_heat_cap", "fan_off", "release_lockout_ends", "night_starts", "night_ends"], 4).map((l) => l.html).join("");

    return `<div class="split"><span class="title">${esc(w.heatPump)}</span><span class="lead">${esc(w.heatPumpLead)}</span></div>
      <div class="grid" style="--min:260px;gap:16px">
        <div style="display:flex;flex-direction:column;gap:14px">
          <span class="eyebrow">${esc(w.releasedFor)}</span>
          <div style="display:flex;flex-direction:column;gap:2px"><span class="big ${releasedFor[1]}">${esc(releasedFor[0])}</span>${releasedSince ? `<span class="lead">${esc(w.since(sinceText(hass, new Date(releasedSince.last_changed))))}</span>` : ""}</div>
          <div class="grid" style="--min:80px;gap:8px">
            ${box(w.heat, heatOn ? w.free : w.locked, heatOn)}
            ${box(w.cool, coolOn ? w.free : w.locked, coolOn)}
            ${box(w.fn, fn ? (hass.formatEntityState ? hass.formatEntityState(fn) : fn.state) : "–", fn && fn.state !== "off")}
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px">
          <span class="eyebrow">${esc(w.whatAndWhy)}</span>
          <div class="row" style="gap:12px;flex-wrap:nowrap"><span class="dot ${running ? "orange pulse" : "grey"}" style="width:12px;height:12px"></span><div style="display:flex;flex-direction:column"><span class="big" style="font-size:22px">${esc(doing)}</span><span class="lead">${esc(meta)}</span></div></div>
          <ul class="checks">${why.map(([ok, text]) => check(ok, text)).join("")}</ul>
          <p class="note-box">${esc(w.deviceDecides + hint)}</p>
        </div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <span class="eyebrow">${esc(w.howClose)}</span>
          ${leverHtml}
        </div>
      </div>
      ${this._timeline(hass, m)}`;
  }

  _timeline(hass, m) {
    const w = words(hass);
    if (!this._data) return "";
    const start = startOfToday();
    const end = new Date(start.getTime() + 86400000);
    const nightStart = String(setting(m.hub, "night_start") || "20:00").split(":").map(Number);
    const nightEnd = String(setting(m.hub, "night_end") || "05:00").split(":").map(Number);
    const frac = ([h, mm]) => (h * 60 + (mm || 0)) / 1440;
    const nights = frac(nightEnd) < frac(nightStart)
      ? [[0, frac(nightEnd)], [frac(nightStart), 1 - frac(nightStart)]]
      : [[frac(nightStart), frac(nightEnd) - frac(nightStart)]];
    const run = spans(this._data.compressor, start, end, RUNNING);
    const fan = spans(this._data.fan, start, end, (s) => Number(s) >= 3);
    const pct = (x) => `${(x * 100).toFixed(2)}%`;
    const now = (Date.now() - start.getTime()) / 86400000;
    return `<div style="display:flex;flex-direction:column;gap:8px">
      <div class="split small muted"><span style="font-weight:500;color:var(--scc-text)">${esc(w.today)}</span>
        <span class="row" style="gap:14px"><span class="row" style="gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:var(--scc-orange)"></span>${esc(w.legendHeats)}</span><span class="row" style="gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:color-mix(in srgb,var(--scc-text) 12%,transparent)"></span>${esc(w.legendNight)}</span><span class="row" style="gap:6px"><span style="width:14px;height:4px;border-radius:2px;background:color-mix(in srgb,var(--scc-blue) 60%,transparent)"></span>${esc(w.legendStage3)}</span></span></div>
      <div class="timeline" role="img" aria-label="${esc(w.today)}">
        <div class="band" style="left:0;right:0;background:var(--scc-well)"></div>
        ${nights.map(([l, wd]) => `<div class="band night" style="left:${pct(l)};width:${pct(wd)}"></div>`).join("")}
        ${run.map(([l, wd]) => `<div class="run" style="left:${pct(l)};width:${pct(wd)}"></div>`).join("")}
        ${fan.map(([l, wd]) => `<div class="fan" style="left:${pct(l)};width:${pct(wd)}"></div>`).join("")}
        <div class="now" style="left:${pct(now)}"></div>
        <div class="ticks"><span>00</span><span>06</span><span>12</span><span>18</span><span>24</span></div>
      </div></div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Auxiliary heaters

class AuxCard extends SccCard {
  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const a = attrs(m.hub);
    const statuses = m.rooms.map((room) => ({ room, status: auxStatus(hass, m.hub, room) }));
    const wgt = statuses.filter((x) => x.status.wgt);
    if (!wgt.length) return null;
    const allowed = wgt.filter((x) => x.status.allowed).length;
    const thr = thresholdsOf(m.hub);

    const gates = [];
    gates.push([a.mode === "heating" && !!a.heat_release, w.heatPump, a.heat_release ? `${w.heat} ${w.free}` : w.locked, ""]);
    if (thr.aux_outdoor) {
      const t = thr.aux_outdoor;
      const ok = t.distance > 0;
      gates.push([ok, w.outdoorCold, w.belowLimit(deg(hass, t.value), deg(hass, t.limit)), ok ? w.lockedFrom(deg(hass, t.limit), kelvin(hass, t.distance)) : ""]);
    }
    const open = m.rooms.filter((room) => attrs(room.state).window_open);
    gates.push([!open.length, w.windows, open.length ? open.map((r) => r.name).join(", ") : w.allClosed, ""]);
    const nightOff = m.rooms.filter((room) => setting(room.state, "aux_heat_off_at_night"));
    gates.push([!(a.is_night && nightOff.length), w.nightGate, nightOff.length ? w.offAtNight(nightOff.map((r) => r.name).join(", ")) : w.noneOffAtNight, ""]);

    const gateHtml = gates.map(([ok, title, now, near]) => `<div class="tile"><span class="row" style="gap:8px;font-size:14px;font-weight:500"><span class="${ok ? "blue" : "orange"}" style="font-weight:700">${ok ? "✓" : "–"}</span>${esc(title)}</span><span class="small" style="color:var(--scc-text)">${esc(now)}</span>${near ? `<span class="small muted">${esc(near)}</span>` : ""}</div>`).join("");

    // The room furthest below its target first: it is the one to look at.
    const gapOf = (room) => (attrs(room.state).target_temperature ?? 0) - (roomTemperature(room.state) ?? 0);
    statuses.sort((x, y) => (y.room.state.attributes.auxiliary_heat ? 99 : gapOf(y.room)) - (x.room.state.attributes.auxiliary_heat ? 99 : gapOf(x.room)));
    const rows = statuses.map(({ room, status }) => {
      const [delta, tone] = deltaText(hass, room);
      const ra = attrs(room.state);
      const next = levers(hass, room.state, ROOM_LEVERS, 1)[0];
      const nextHtml = next ? next.html : "";
      return `<tr>
        <th scope="row" style="white-space:nowrap">${link(roomView(room), esc(room.name))}</th>
        <td class="mono" style="white-space:nowrap">${esc(num(hass, roomTemperature(room.state)))} / ${esc(num(hass, ra.target_temperature))}<div class="small ${tone}">${esc(delta)}</div></td>
        <td>${status.wgt ? pill(status.allowed ? w.mayYes : w.mayNo, status.allowed ? "blue" : "orange") : pill(status.why, "grey")}</td>
        <td><span class="row" style="gap:6px">${pill(status.state, status.tone)}<span class="narrow-only">${status.wgt ? pill(status.allowed ? w.mayYes : w.mayNo, status.allowed ? "blue" : "orange") : ""}</span></span><div class="small muted" style="margin-top:4px;line-height:1.4">${status.wgt ? esc(status.why) : ""}</div></td>
        <td style="min-width:220px">${nextHtml}</td>
      </tr>`;
    }).join("");

    const mayText = allowed === wgt.length ? w.yesAll : allowed === 0 ? w.noneMay : w.someMay(allowed, wgt.length);
    return `<div class="split"><span class="title">${esc(w.aux)}</span><span class="lead">${esc(a.auxiliary_heat_house ? w.auxHouseOn : w.auxHouseOff)}</span></div>
      <div class="split"><span class="eyebrow">${esc(w.mayRun)}</span><span style="font-weight:500" class="${allowed ? "blue" : "orange"}">${esc(mayText)}</span></div>
      <div class="grid" style="--min:150px">${gateHtml}</div>
      <div class="scroll"><table class="stack"><thead><tr><th>${esc(w.room)}</th><th>${esc(w.actualTarget)}</th><th>${esc(w.may)}</th><th>${esc(w.runs)}</th><th>${esc(w.nextChange)}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Diagnosis: why a room, or the house, is cold or warm

const DIAGNOSIS = {
  de: {
    roomCold: "Warum ist es hier kühl?",
    roomWarm: "Warum ist es hier warm?",
    roomFine: "Der Raum ist auf Soll.",
    actual: "Ist",
    target: "Soll",
    gap: "Abstand",
    setpointQ: "Ist der Sollwert niedrig?",
    setpointNo: (v) => `Nein, ${v.day} am Tag, ${v.night} nachts.`,
    setpointNight: (v) => `Ja, gerade gilt die Nachtabsenkung: ${v.night} bis ${v.end}.`,
    setpointHoliday: (v) => `Ja, Urlaub: ${v.target}.`,
    setpointShort: "Gerade gilt ein abgesenkter Sollwert.",
    nightQ: "Wirkt die Nacht nach?",
    nightYes: (v) => `Ja. Von ${v.start} bis ${v.end} fiel der Raum von ${v.from} auf ${v.to}.`,
    nightNo: (v) => `Nein, nach der Nacht lag der Raum bei ${v.to}.`,
    nightNow: "Es ist Nacht, die Nachtwerte gelten.",
    nightShort: (v) => `Die Nacht hat den Raum auf ${v.to} gebracht.`,
    windowQ: "War ein Fenster offen?",
    windowNow: "Ja, gerade offen.",
    windowEarlier: (v) => `Um ${v.time} offen, jetzt zu.`,
    windowNo: "Nein, in den letzten 3 Stunden nicht.",
    windowNone: "Dem Raum ist kein Kontakt zugeordnet.",
    windowShort: "Ein Fenster ist offen.",
    hpQ: "Liefert die Wärmepumpe nicht?",
    hpYes: (v) => `Doch: sie heizt seit ${v.since}, die Zuluft hat ${v.supply}, ${v.lift} mehr als der Raum.`,
    hpIdle: "Sie ist freigegeben, heizt aber gerade nicht. Start und Stopp entscheidet die WGT.",
    hpLocked: (v) => `Sie ist nicht freigegeben. ${v.reason}`,
    hpIdleShort: "Die Wärmepumpe heizt gerade nicht.",
    hpLockedShort: "Die Wärmepumpe ist nicht freigegeben.",
    airQ: "Reicht die warme Luft?",
    airNo: (v) => `Nein. Die Zuluft ist ${v.lift} wärmer, aber der Raum stieg nur ${v.rise} in ${v.minutes}.`,
    airYes: (v) => `Ja, der Raum steigt: ${v.rise} in ${v.minutes}.`,
    airUnknown: "Lässt sich gerade nicht sagen, der Raum wird nicht beobachtet.",
    airStalled: "Nein, mit der Zuluft allein holt der Raum nicht auf.",
    airShort: "Die warme Luft reicht nicht, um aufzuholen.",
    auxQ: "Hilft der Zuheizer?",
    auxOn: "Ja, er läuft.",
    auxWait: (v) => `Gleich: er geht um ${v.time} an.`,
    auxVerdict: (v) => `Er darf, wartet aber auf das Urteil um ${v.time}: steigt der Raum bis dahin nicht um ${v.need}, geht er 15 min später an.`,
    auxLocked: (v) => `Er ist gesperrt. ${v.why}`,
    auxSmall: (v) => `Noch nicht: der Raum ist ${v.deficit} unter Soll, der Zuheizer kommt ab ${v.start}.`,
    auxNone: "Der Raum hat keinen Zuheizer der WGT.",
    auxLockedShort: "Der Zuheizer ist gesperrt.",
    auxWaitShort: "Der Zuheizer wartet noch auf sein Urteil.",
    noCause: (v) => `Keine eindeutige Ursache: der Raum liegt ${v.gap} unter Soll.`,
    boostQ: "Ist der Sollwert angehoben?",
    boostYes: (v) => `Ja, PV-Überschuss hebt ihn um ${v.boost} an.`,
    boostNo: (v) => `Nein, ${v.target}.`,
    boostShort: "Der Sollwert ist wegen PV-Überschuss angehoben.",
    heatingQ: "Heizt die Wärmepumpe?",
    heatingYes: (v) => `Ja. Die Zuluft geht mit ${v.supply} in jeden Raum, auch in die, die schon warm genug sind.`,
    heatingNo: "Nein.",
    heatingShort: "Die Zuluft heizt alle Räume gleich, auch die schon warmen.",
    auxRunQ: "Läuft der Zuheizer?",
    auxRunYes: "Ja.",
    auxRunNo: "Nein.",
    auxRunShort: "Der Zuheizer läuft.",
    outsideQ: "Ist es draußen wärmer?",
    outsideYes: (v) => `Ja, ${v.outdoor} draußen, ${v.excess} mehr als in der Abluft.`,
    outsideNo: (v) => `Nein, ${v.outdoor}.`,
    outsideShort: "Draußen ist es wärmer als drinnen.",
    otherQ: "Sonne, Kochen, Personen?",
    otherA: "Sieht der Controller nicht. Ein Raum, der ohne Heizen steigt, deutet darauf hin.",
    steps: {
      allowed: "Darf laufen",
      needs: "Raum braucht Wärme",
      catching: "Holt der Raum auf?",
      wait: "15 min Wartezeit",
      on: "An",
      needsDetail: (v) => `${v.deficit} unter Soll, ab ${v.start}`,
      catchingDetail: (v) => `+${v.rise} seit ${v.since}, nötig ${v.need} bis ${v.until}`,
      catchingDone: "Nein, oder die Zuluft zählt nicht",
      waitDetail: (v) => `noch ${v.left}`,
      onDetail: "bis der Sollwert erreicht ist",
    },
    houseVerdictNo: "Nein. Alle Räume sind auf Soll.",
    houseVerdictSome: "Ein wenig.",
    houseVerdictYes: "Ja.",
    houseWarmNo: "Nein. Kein Raum liegt deutlich über Soll.",
    releaseQ: "Ist die Wärmepumpe freigegeben?",
    releaseYes: (v) => `Ja, zum Heizen, seit ${v.since}.`,
    releaseNo: (v) => `Nein. ${v.reason}`,
    releaseShort: "Die Wärmepumpe ist nicht freigegeben.",
    runtimeQ: "Läuft sie lange genug?",
    runtimeShort: "Die Wärmepumpe läuft zu wenig.",
    runtimeLow: (v) => `Nein. Heute ${v.hours}${v.nightZero ? ", nachts nie" : ""}.`,
    runtimeOk: (v) => `Heute ${v.hours}.`,
    auxHelpQ: "Helfen die Zuheizer?",
    auxHelpOn: (v) => `${v.n} laufen: ${v.names}.`,
    auxHelpWait: (v) => `${v.names} warten.`,
    auxHelpNone: "Keiner läuft.",
    windowsQ: "Fenster offen?",
    windowsOpen: (v) => `${v.names} offen.`,
    windowsShort: "Fenster sind offen.",
    windowsClosed: "Alle zu.",
    recoveryQ: "Wärmerückgewinnung?",
    recoveryClosed: (v) => `Bypass zu${v.recovery ? `, Rückgewinnung ${v.recovery}` : ""}. Die Abluftwärme bleibt im Haus.`,
    recoveryOpen: "Bypass offen: die Abluftwärme geht hinaus.",
    recoveryUnknown: "Kein Bypass-Sensor gewählt.",
    recoveryShort: "Der Bypass ist offen.",
    fanQ: "Lüftung zu stark?",
    fanA: (v) => v.text,
    targetsQ: "Sollwerte?",
    setbackQ: "Nachtabsenkung?",
    setbackOn: (v) => `An: Nachtwerte von ${v.start} bis ${v.end}.`,
    setbackOff: "Aus.",
    holidayQ: "Urlaub?",
    holidayOn: "An: abgesenkte Sollwerte.",
    holidayOff: "Aus.",
    holidayShort: "Urlaub ist an.",
    otherwise: (v) => `sonst ${v}`,
    coolingQ: "Kann gekühlt werden?",
    coolingOn: "Ja, Kühlen ist freigegeben.",
    coolingWaits: (v) => `Kühlmodus an, aber noch nicht freigegeben. ${v.reason}`,
    coolingOff: "Nein, der Modus ist nicht Kühlen.",
  },
  en: {
    roomCold: "Why is it cool in here?",
    roomWarm: "Why is it warm in here?",
    roomFine: "The room is at target.",
    actual: "Actual",
    target: "Target",
    gap: "Gap",
    setpointQ: "Is the target low?",
    setpointNo: (v) => `No, ${v.day} by day, ${v.night} at night.`,
    setpointNight: (v) => `Yes, the night setback applies: ${v.night} until ${v.end}.`,
    setpointHoliday: (v) => `Yes, holiday: ${v.target}.`,
    setpointShort: "A lowered target applies right now.",
    nightQ: "Is the night still showing?",
    nightYes: (v) => `Yes. From ${v.start} to ${v.end} the room fell from ${v.from} to ${v.to}.`,
    nightNo: (v) => `No, after the night the room was at ${v.to}.`,
    nightNow: "It is night, the night values apply.",
    nightShort: (v) => `The night took the room down to ${v.to}.`,
    windowQ: "Was a window open?",
    windowNow: "Yes, open right now.",
    windowEarlier: (v) => `Open at ${v.time}, closed now.`,
    windowNo: "No, not in the last 3 hours.",
    windowNone: "The room has no contact.",
    windowShort: "A window is open.",
    hpQ: "Is the heat pump not delivering?",
    hpYes: (v) => `It is: heating since ${v.since}, supply air at ${v.supply}, ${v.lift} above the room.`,
    hpIdle: "It is released, but not heating right now. The unit decides when it starts and stops.",
    hpLocked: (v) => `It is not released. ${v.reason}`,
    hpIdleShort: "The heat pump is not heating right now.",
    hpLockedShort: "The heat pump is not released.",
    airQ: "Is the warm air enough?",
    airNo: (v) => `No. The supply air is ${v.lift} warmer, but the room rose only ${v.rise} in ${v.minutes}.`,
    airYes: (v) => `Yes, the room is rising: ${v.rise} in ${v.minutes}.`,
    airUnknown: "Cannot tell right now, the room is not being watched.",
    airStalled: "No, the room does not catch up on supply air alone.",
    airShort: "The warm air is not enough to catch up.",
    auxQ: "Is the aux heater helping?",
    auxOn: "Yes, it is running.",
    auxWait: (v) => `Shortly: it goes on at ${v.time}.`,
    auxVerdict: (v) => `It may, but waits for the verdict at ${v.time}: if the room has not risen ${v.need} by then, it goes on 15 min later.`,
    auxLocked: (v) => `It is locked. ${v.why}`,
    auxSmall: (v) => `Not yet: the room is ${v.deficit} below target, the heater comes from ${v.start}.`,
    auxNone: "The room has no aux heater of the unit.",
    auxLockedShort: "The aux heater is locked.",
    auxWaitShort: "The aux heater is still waiting for its verdict.",
    noCause: (v) => `No clear cause: the room is ${v.gap} below target.`,
    boostQ: "Is the target raised?",
    boostYes: (v) => `Yes, PV surplus raises it by ${v.boost}.`,
    boostNo: (v) => `No, ${v.target}.`,
    boostShort: "The target is raised for PV surplus.",
    heatingQ: "Is the heat pump heating?",
    heatingYes: (v) => `Yes. The supply air goes into every room at ${v.supply}, also those already warm enough.`,
    heatingNo: "No.",
    heatingShort: "The supply air heats every room alike, also the warm ones.",
    auxRunQ: "Is the aux heater running?",
    auxRunYes: "Yes.",
    auxRunNo: "No.",
    auxRunShort: "The aux heater is running.",
    outsideQ: "Is it warmer outdoors?",
    outsideYes: (v) => `Yes, ${v.outdoor} outdoors, ${v.excess} above the extract air.`,
    outsideNo: (v) => `No, ${v.outdoor}.`,
    outsideShort: "It is warmer outdoors than indoors.",
    otherQ: "Sun, cooking, people?",
    otherA: "The controller cannot see these. A room that warms without heating points to them.",
    steps: {
      allowed: "Allowed to run",
      needs: "Room needs heat",
      catching: "Is the room catching up?",
      wait: "15 min wait",
      on: "On",
      needsDetail: (v) => `${v.deficit} below target, from ${v.start}`,
      catchingDetail: (v) => `+${v.rise} since ${v.since}, needs ${v.need} by ${v.until}`,
      catchingDone: "No, or the supply air does not count",
      waitDetail: (v) => `${v.left} to go`,
      onDetail: "until the target is reached",
    },
    houseVerdictNo: "No. Every room is at target.",
    houseVerdictSome: "A little.",
    houseVerdictYes: "Yes.",
    houseWarmNo: "No. No room is clearly above target.",
    releaseQ: "Is the heat pump released?",
    releaseYes: (v) => `Yes, for heating, since ${v.since}.`,
    releaseNo: (v) => `No. ${v.reason}`,
    releaseShort: "The heat pump is not released.",
    runtimeQ: "Is it running long enough?",
    runtimeShort: "The heat pump runs too little.",
    runtimeLow: (v) => `No. Today ${v.hours}${v.nightZero ? ", never at night" : ""}.`,
    runtimeOk: (v) => `Today ${v.hours}.`,
    auxHelpQ: "Are the aux heaters helping?",
    auxHelpOn: (v) => `${v.n} running: ${v.names}.`,
    auxHelpWait: (v) => `${v.names} waiting.`,
    auxHelpNone: "None is running.",
    windowsQ: "Windows open?",
    windowsOpen: (v) => `${v.names} open.`,
    windowsShort: "Windows are open.",
    windowsClosed: "All closed.",
    recoveryQ: "Heat recovery?",
    recoveryClosed: (v) => `Bypass closed${v.recovery ? `, recovering ${v.recovery}` : ""}. The extract heat stays in the house.`,
    recoveryOpen: "Bypass open: the extract heat goes outside.",
    recoveryUnknown: "No bypass sensor chosen.",
    recoveryShort: "The bypass is open.",
    fanQ: "Too much ventilation?",
    fanA: (v) => v.text,
    targetsQ: "Targets?",
    setbackQ: "Night setback?",
    setbackOn: (v) => `On: night values from ${v.start} to ${v.end}.`,
    setbackOff: "Off.",
    holidayQ: "Holiday?",
    holidayOn: "On: lowered targets.",
    holidayOff: "Off.",
    holidayShort: "Holiday is on.",
    otherwise: (v) => `otherwise ${v}`,
    coolingQ: "Can it cool?",
    coolingOn: "Yes, cooling is released.",
    coolingWaits: (v) => `Cooling mode on, but not released yet. ${v.reason}`,
    coolingOff: "No, the mode is not cooling.",
  },
};

function dx(hass) {
  return DIAGNOSIS[lang(hass)];
}

function findRoom(m, config) {
  const wanted = String(config.room || "");
  return m.rooms.find((room) => room.id === wanted || room.name === wanted || slug(room.name) === slug(wanted));
}

function lastNight(hass, state) {
  const [sh, sm] = String(setting(state, "night_start") || "20:00").split(":").map(Number);
  const [eh, em] = String(setting(state, "night_end") || "05:00").split(":").map(Number);
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), eh, em || 0);
  if (end > now) end.setDate(end.getDate() - 1);
  const start = new Date(end.getFullYear(), end.getMonth(), end.getDate(), sh, sm || 0);
  if (start >= end) start.setDate(start.getDate() - 1);
  return { start, end };
}

function valueAt(series, at) {
  let found = null;
  for (const row of series) {
    if (row.t <= at) found = row;
    else break;
  }
  return found ? found.v : null;
}

function header(hass, title, lead, figures) {
  const w = words(hass);
  return `<a class="nav row" style="gap:6px;font-size:14px;min-height:32px" href="${esc(viewPath("overview"))}" data-view="overview">${ICONS.back}${esc(w.back)}</a>
    <div class="split" style="align-items:flex-end"><div style="display:flex;flex-direction:column;gap:4px"><span class="big" style="font-size:26px">${esc(title)}</span>${lead ? `<span class="lead">${esc(lead)}</span>` : ""}</div>
    <div class="figures">${figures.map(([label, value, tone]) => `<div class="figure"><span class="small muted">${esc(label)}</span><span class="v ${tone || ""}">${esc(value)}</span></div>`).join("")}</div></div>`;
}

function statement(hass, text) {
  const w = words(hass);
  return `<div style="display:flex;flex-direction:column;gap:6px"><span class="eyebrow">${esc(w.inShort)}</span><p class="statement">${esc(text)}</p></div>`;
}

class RoomCard extends SccCard {
  async fetch(hass) {
    const m = model(hass);
    const room = findRoom(m, this._config);
    if (!room || !m.hub) return null;
    const src = attrs(room.state).sources || {};
    const day = new Date(Date.now() - 24 * 3600000);
    const compressor = (attrs(m.hub).sources || {}).compressor;
    const [withAttrs, plain] = await Promise.all([
      history(hass, [src.climate], day, new Date(), true),
      history(hass, [src.temperature !== src.climate ? src.temperature : null, compressor, ...(src.contacts || [])], day),
    ]);
    const climate = (withAttrs || {})[src.climate] || [];
    const temperature = src.temperature && src.temperature !== src.climate
      ? ((plain || {})[src.temperature] || []).map((r) => ({ t: r.t, v: Number(r.s) })).filter((r) => Number.isFinite(r.v))
      : climate.map((r) => ({ t: r.t, v: Number(r.a?.current_temperature) })).filter((r) => Number.isFinite(r.v));
    const target = climate.map((r) => ({ t: r.t, v: Number(r.a?.temperature) })).filter((r) => Number.isFinite(r.v));
    const contacts = (src.contacts || []).map((id) => (plain || {})[id] || []);
    return { temperature, target, compressor: (plain || {})[compressor] || [], contacts };
  }

  content(hass, m) {
    const room = findRoom(m, this._config);
    if (!room || !m.hub) return `<p class="empty">${esc(this._config.room || "")}</p>`;
    const w = words(hass);
    const d = dx(hass);
    const a = attrs(room.state);
    const temperature = roomTemperature(room.state);
    const target = a.target_temperature;
    const gap = temperature !== null && target != null ? temperature - target : null;
    const figures = [
      [d.actual, deg(hass, temperature)],
      [d.target, deg(hass, target)],
      [d.gap, gap === null ? "–" : `${gap >= 0 ? "+" : "−"}${kelvin(hass, Math.abs(gap))}`, gap !== null && gap <= -0.5 ? "orange" : ""],
    ];
    const cold = gap !== null && gap <= -0.2;
    const warm = gap !== null && gap >= 0.5;
    const causes = cold ? this._cold(hass, m, room) : warm ? this._warm(hass, m, room) : [];
    const shorts = causes.filter((c) => c.short).map((c) => c.short);
    const text = !cold && !warm ? d.roomFine : shorts.length ? shorts.join(" ") : d.noCause({ gap: kelvin(hass, Math.abs(gap)) });

    const status = auxStatus(hass, m.hub, room);
    const next = levers(hass, room.state, ROOM_LEVERS, 5).map((l) => l.html).join("");
    return `${header(hass, room.name, cold ? d.roomCold : warm ? d.roomWarm : "", figures)}
      ${statement(hass, text)}
      <div class="grid" style="--min:320px;gap:20px;align-items:start">
        ${causes.length ? `<div style="display:flex;flex-direction:column;gap:12px"><span class="eyebrow">${esc(w.causes)}</span><ol class="causes">${causes.map((c) => cause(hass, c.kind, c.q, c.a)).join("")}</ol></div>` : ""}
        <div style="display:flex;flex-direction:column;gap:20px">
          ${status.wgt && attrs(m.hub).mode === "heating" ? `<div style="display:flex;flex-direction:column;gap:12px"><span class="eyebrow">${esc(w.auxPath)}</span>${this._steps(hass, m, room)}</div>` : ""}
          ${next ? `<div style="display:flex;flex-direction:column;gap:14px"><span class="eyebrow">${esc(w.whatNext)}</span>${next}</div>` : ""}
        </div>
      </div>
      ${this._chart(hass, m, room)}`;
  }

  _cold(hass, m, room) {
    const d = dx(hass);
    const a = attrs(room.state);
    const hub = attrs(m.hub);
    const out = [];
    const temperature = roomTemperature(room.state);
    const day = setting(room.state, "target_normal");
    const night = setting(room.state, "target_night");
    const up = upcomingOf(room.state);
    if (a.reason_code === "night_setback") {
      out.push({ kind: "yes", q: d.setpointQ, a: d.setpointNight({ night: deg(hass, night), end: up.night_ends ? clock(hass, up.night_ends) : "" }), short: d.setpointShort });
    } else if (a.reason_code === "holiday") {
      out.push({ kind: "yes", q: d.setpointQ, a: d.setpointHoliday({ target: deg(hass, a.target_temperature) }), short: d.setpointShort });
    } else {
      out.push({ kind: "no", q: d.setpointQ, a: d.setpointNo({ day: deg(hass, day), night: deg(hass, night) }) });
    }

    const series = this._data?.temperature || [];
    if (hub.is_night) {
      out.push({ kind: "part", q: d.nightQ, a: d.nightNow });
    } else if (series.length) {
      const { start, end } = lastNight(hass, room.state);
      const from = valueAt(series, start);
      const to = valueAt(series, end);
      if (from !== null && to !== null) {
        const fell = from - to >= 0.3 && day - to >= 0.5 && Date.now() - end.getTime() < 10 * 3600000;
        out.push(fell
          ? { kind: "yes", q: d.nightQ, a: d.nightYes({ start: clock(hass, start), end: clock(hass, end), from: deg(hass, from), to: deg(hass, to) }), short: d.nightShort({ to: deg(hass, to) }) }
          : { kind: "no", q: d.nightQ, a: d.nightNo({ to: deg(hass, to) }) });
      }
    }

    const contacts = (a.sources || {}).contacts || [];
    if (!contacts.length) {
      out.push({ kind: "unknown", q: d.windowQ, a: d.windowNone });
    } else if (a.window_open) {
      out.push({ kind: "yes", q: d.windowQ, a: d.windowNow, short: d.windowShort });
    } else {
      const since = Date.now() - 3 * 3600000;
      const opened = (this._data?.contacts || []).flat().filter((r) => r.s === "on" && r.t.getTime() >= since).sort((x, y) => y.t - x.t)[0];
      out.push(opened ? { kind: "part", q: d.windowQ, a: d.windowEarlier({ time: clock(hass, opened.t) }) } : { kind: "no", q: d.windowQ, a: d.windowNo });
    }

    const compressor = source(hass, m.hub, "compressor");
    const supply = numberOf(source(hass, m.hub, "supply_air"));
    const running = compressor && RUNNING(compressor.state);
    if (hub.mode === "heating") {
      if (!hub.heat_release) {
        const reason = say(hass).reason[hub.reason_code];
        out.push({ kind: "yes", q: d.hpQ, a: d.hpLocked({ reason: reason ? reason({ outdoor: deg(hass, hub.outdoor_temperature), limit: deg(hass, setting(m.hub, "heat_release_below")), forecast: "", coolLimit: "" }) : "" }), short: d.hpLockedShort });
      } else if (!running) {
        out.push({ kind: "yes", q: d.hpQ, a: d.hpIdle, short: d.hpIdleShort });
      } else {
        out.push({ kind: "no", q: d.hpQ, a: d.hpYes({ since: sinceText(hass, new Date(compressor.last_changed)), supply: deg(hass, supply), lift: kelvin(hass, supply !== null && temperature !== null ? supply - temperature : null) }) });
      }

      const thr = thresholdsOf(room.state);
      if (gate(room.state, "aux_not_catching_up")?.passed) {
        out.push({ kind: "yes", q: d.airQ, a: d.airStalled, short: d.airShort });
      } else if (thr.aux_rise && up.aux_verdict) {
        const startAt = new Date(up.aux_verdict.getTime() - 30 * 60000);
        const minutes = duration(hass, Date.now() - startAt.getTime());
        const rising = thr.aux_rise.value >= thr.aux_rise.limit / 2;
        out.push(rising
          ? { kind: "no", q: d.airQ, a: d.airYes({ rise: kelvin(hass, thr.aux_rise.value), minutes }) }
          : { kind: "yes", q: d.airQ, a: d.airNo({ lift: kelvin(hass, thr.aux_supply?.value), rise: kelvin(hass, thr.aux_rise.value), minutes }), short: d.airShort });
      } else if (running) {
        out.push({ kind: "unknown", q: d.airQ, a: d.airUnknown });
      }

      const status = auxStatus(hass, m.hub, room);
      if (!status.wgt) {
        out.push({ kind: "unknown", q: d.auxQ, a: d.auxNone });
      } else if (a.auxiliary_heat) {
        out.push({ kind: "no", q: d.auxQ, a: d.auxOn });
      } else if (!status.allowed) {
        out.push({ kind: "yes", q: d.auxQ, a: d.auxLocked({ why: status.why }), short: d.auxLockedShort });
      } else if (up.aux_on) {
        out.push({ kind: "wait", q: d.auxQ, a: d.auxWait({ time: clock(hass, up.aux_on) }) });
      } else if (up.aux_verdict) {
        out.push({ kind: "wait", q: d.auxQ, a: d.auxVerdict({ time: clock(hass, up.aux_verdict), need: kelvin(hass, thr.aux_rise?.limit ?? 0.2) }), short: d.auxWaitShort });
      } else {
        const start = setting(room.state, "aux_deficit") ?? 0.5;
        out.push({ kind: "no", q: d.auxQ, a: d.auxSmall({ deficit: kelvin(hass, a.target_temperature - temperature), start: kelvin(hass, start) }) });
      }
    }
    return out;
  }

  _warm(hass, m, room) {
    const d = dx(hass);
    const a = attrs(room.state);
    const hub = attrs(m.hub);
    const out = [];
    if (a.reason_code === "surplus") {
      out.push({ kind: "yes", q: d.boostQ, a: d.boostYes({ boost: kelvin(hass, setting(m.hub, "surplus_target_boost") ?? 1) }), short: d.boostShort });
    } else {
      out.push({ kind: "no", q: d.boostQ, a: d.boostNo({ target: deg(hass, a.target_temperature) }) });
    }
    const compressor = source(hass, m.hub, "compressor");
    const heating = hub.mode === "heating" && compressor && RUNNING(compressor.state);
    out.push(heating
      ? { kind: "yes", q: d.heatingQ, a: d.heatingYes({ supply: deg(hass, numberOf(source(hass, m.hub, "supply_air"))) }), short: d.heatingShort }
      : { kind: "no", q: d.heatingQ, a: d.heatingNo });
    if (a.auxiliary_heat !== null && a.auxiliary_heat !== undefined) {
      out.push(a.auxiliary_heat ? { kind: "yes", q: d.auxRunQ, a: d.auxRunYes, short: d.auxRunShort } : { kind: "no", q: d.auxRunQ, a: d.auxRunNo });
    }
    const excess = thresholdsOf(m.hub).fan_heat_cap?.value;
    const outdoor = hub.outdoor_temperature;
    out.push(excess !== undefined && excess > 0
      ? { kind: "yes", q: d.outsideQ, a: d.outsideYes({ outdoor: deg(hass, outdoor), excess: kelvin(hass, excess) }), short: d.outsideShort }
      : { kind: "no", q: d.outsideQ, a: d.outsideNo({ outdoor: deg(hass, outdoor) }) });
    out.push({ kind: "unknown", q: d.otherQ, a: d.otherA });
    return out;
  }

  _steps(hass, m, room) {
    const d = dx(hass).steps;
    const a = attrs(room.state);
    const thr = thresholdsOf(room.state);
    const up = upcomingOf(room.state);
    const status = auxStatus(hass, m.hub, room);
    const temperature = roomTemperature(room.state);
    const start = setting(room.state, "aux_deficit") ?? 0.5;
    const deficit = temperature !== null ? a.target_temperature - temperature : 0;
    const on = !!a.auxiliary_heat;
    const needs = on || deficit >= start;
    const decided = ["aux_override", "aux_supply_insufficient", "aux_not_catching_up"].some((name) => gate(room.state, name)?.passed);
    const watching = !!thr.aux_rise;
    const waiting = !!up.aux_on;
    const list = [
      [status.allowed ? "done" : "now", d.allowed, status.allowed ? "" : status.why],
      [needs ? "done" : status.allowed ? "now" : "todo", d.needs, d.needsDetail({ deficit: kelvin(hass, Math.max(0, deficit)), start: kelvin(hass, start) })],
      [on || waiting || decided ? "done" : watching ? "now" : "todo", d.catching, watching && up.aux_verdict
        ? d.catchingDetail({ rise: kelvin(hass, thr.aux_rise.value), since: clock(hass, new Date(up.aux_verdict.getTime() - 30 * 60000)), need: kelvin(hass, thr.aux_rise.limit), until: clock(hass, up.aux_verdict) })
        : decided || on || waiting ? d.catchingDone : ""],
      [on ? "done" : waiting ? "now" : "todo", d.wait, waiting ? d.waitDetail({ left: duration(hass, up.aux_on.getTime() - Date.now()) }) : ""],
      [on ? "done" : "todo", d.on, waiting ? clock(hass, up.aux_on) : d.onDetail],
    ];
    return `<ol class="steps">${list.map(([state, title, detail], i) => `<li><div class="rail"><span class="node ${state}">${state === "done" ? "✓" : i + 1}</span><span class="line ${state === "done" ? "done" : ""}"></span></div><div class="body"><span style="font-size:14px;font-weight:500">${esc(title)}</span>${detail ? `<span class="small muted" style="line-height:1.4">${esc(detail)}</span>` : ""}</div></li>`).join("")}</ol>`;
  }

  _chart(hass, m, room) {
    const w = words(hass);
    const series = this._data?.temperature || [];
    if (series.length < 2) return "";
    const end = Date.now();
    const start = end - 24 * 3600000;
    const targets = this._data.target || [];
    const values = [...series.map((r) => r.v), ...targets.map((r) => r.v)];
    const lo = Math.floor(Math.min(...values) - 0.3);
    const hi = Math.ceil(Math.max(...values) + 0.3);
    const W = 1000;
    const H = 180;
    const x = (t) => ((Math.max(start, t) - start) / (end - start)) * W;
    const y = (v) => H - ((v - lo) / (hi - lo)) * H;
    const line = (rows) => {
      const pts = [];
      let prev = null;
      for (const r of rows) {
        if (prev !== null) pts.push(`${x(r.t.getTime()).toFixed(1)},${y(prev).toFixed(1)}`);
        pts.push(`${x(r.t.getTime()).toFixed(1)},${y(r.v).toFixed(1)}`);
        prev = r.v;
      }
      if (prev !== null) pts.push(`${W},${y(prev).toFixed(1)}`);
      return pts.join(" ");
    };
    const smooth = (rows) => [`${x(rows[0].t.getTime()).toFixed(1)},${y(rows[0].v).toFixed(1)}`, ...rows.slice(1).map((r) => `${x(r.t.getTime()).toFixed(1)},${y(r.v).toFixed(1)}`), `${W},${y(rows[rows.length - 1].v).toFixed(1)}`].join(" ");
    const { start: ns, end: ne } = lastNight(hass, room.state);
    const runs = spans(this._data.compressor || [], new Date(start), new Date(end), RUNNING);
    const grid = [];
    for (let v = lo; v <= hi; v += 1) grid.push(`<line x1="0" x2="${W}" y1="${y(v)}" y2="${y(v)}" stroke="var(--scc-line)"></line><text x="4" y="${y(v) - 4}">${esc(num(hass, v, 0))} °C</text>`);
    return `<div style="display:flex;flex-direction:column;gap:10px">
      <div class="split"><span class="eyebrow">${esc(w.last24)}</span><span class="row small muted" style="gap:14px"><span class="row" style="gap:6px"><span style="width:16px;height:3px;background:var(--scc-text)"></span>${esc(w.roomLine)}</span><span class="row" style="gap:6px"><span style="width:16px;border-top:2px dashed var(--scc-blue)"></span>${esc(w.targetLine)}</span><span class="row" style="gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:var(--scc-orange)"></span>${esc(w.legendHeats)}</span></span></div>
      <svg viewBox="0 0 ${W} ${H + 40}" style="width:100%;height:auto" role="img" aria-label="${esc(w.last24)}">
        <rect x="${x(ns.getTime())}" y="0" width="${Math.max(0, x(ne.getTime()) - x(ns.getTime()))}" height="${H}" fill="var(--scc-well)"></rect>
        ${grid.join("")}
        ${targets.length ? `<polyline points="${line(targets)}" fill="none" stroke="var(--scc-blue)" stroke-width="2" stroke-dasharray="6 5"></polyline>` : ""}
        <polyline points="${smooth(series)}" fill="none" stroke="var(--scc-text)" stroke-width="2.5" stroke-linejoin="round"></polyline>
        ${runs.map(([l, wd]) => `<rect x="${l * W}" y="${H + 8}" width="${Math.max(1, wd * W)}" height="10" rx="2" fill="var(--scc-orange)"></rect>`).join("")}
        <text x="0" y="${H + 36}">${esc(clock(hass, new Date(start)))}</text>
        <text x="${x(ns.getTime())}" y="${H + 36}">${esc(clock(hass, ns))}</text>
        <text x="${x(ne.getTime())}" y="${H + 36}">${esc(clock(hass, ne))}</text>
        <text x="${W - 34}" y="${H + 36}">${esc(w.now)}</text>
      </svg></div>`;
  }
}

class HouseCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    return [...super.watched(hass), m.own.night_setback?.entity_id, m.own.holiday?.entity_id, m.own.heat_recovery?.entity_id].filter(Boolean);
  }

  async fetch(hass) {
    const m = model(hass);
    if (!m.hub) return null;
    const s = attrs(m.hub).sources || {};
    const end = new Date();
    const start = new Date(startOfToday().getTime() - 6 * 86400000);
    const [stats, runs] = await Promise.all([
      statistics(hass, [s.extract], start, end, "day"),
      history(hass, [s.compressor], start),
    ]);
    return { extract: (stats || {})[s.extract] || [], compressor: (runs || {})[s.compressor] || [] };
  }

  content(hass, m) {
    if (!m.hub) return null;
    const warm = this._config.variant === "warm";
    const w = words(hass);
    const d = dx(hass);
    const hub = attrs(m.hub);
    const temps = m.rooms.map((room) => ({ room, t: roomTemperature(room.state), target: attrs(room.state).target_temperature })).filter((x) => x.t !== null);
    temps.sort((x, y) => x.t - y.t);
    const extreme = warm ? temps[temps.length - 1] : temps[0];
    const figures = [
      [warm ? w.warmest : w.coldest, extreme ? `${deg(hass, extreme.t)}` : "–", ""],
      [w.houseExtract, deg(hass, numberOf(source(hass, m.hub, "extract")))],
      [w.outdoor, deg(hass, hub.outdoor_temperature)],
    ];
    const groups = warm ? this._warm(hass, m) : this._cold(hass, m);
    const shorts = groups.flatMap((g) => g.items).filter((c) => c.short).map((c) => c.short);
    const off = temps.filter((x) => x.target != null && (warm ? x.t - x.target >= 0.5 : x.target - x.t >= 0.5));
    let verdict;
    if (warm) verdict = off.length ? `${off.length > 1 ? d.houseVerdictYes : d.houseVerdictSome} ${shorts.join(" ")}` : d.houseWarmNo;
    else verdict = off.length ? `${off.length > 1 ? d.houseVerdictYes : d.houseVerdictSome} ${shorts.join(" ")}` : d.houseVerdictNo;

    return `${header(hass, warm ? w.houseWarm : w.houseCold, "", figures)}
      ${statement(hass, verdict.trim())}
      ${warm ? "" : this._balance(hass)}
      <div class="grid" style="--min:300px;gap:20px;align-items:start">
        ${groups.map((g) => `<div style="display:flex;flex-direction:column;gap:12px"><span class="eyebrow">${esc(g.title)}</span><ol class="causes">${g.items.map((c) => cause(hass, c.kind, c.q, c.a)).join("")}</ol></div>`).join("")}
      </div>`;
  }

  _cold(hass, m) {
    const w = words(hass);
    const d = dx(hass);
    const hub = attrs(m.hub);
    const heatSwitch = source(hass, m.hub, "heat_release");
    const released = heatSwitch ? heatSwitch.state === "on" : !!hub.heat_release;
    const reason = say(hass).reason[hub.reason_code];
    const below = m.rooms.filter((room) => attrs(room.state).target_temperature - roomTemperature(room.state) >= 0.5);
    const runs = this._data?.compressor || [];
    const today = runs.length ? hoursIn(runs, startOfToday(), new Date(), RUNNING) : null;
    const { start: ns, end: ne } = lastNight(hass, m.hub);
    const nightHours = runs.length ? hoursIn(runs, ns, ne, RUNNING) : null;
    const wgt = m.rooms.filter((room) => auxStatus(hass, m.hub, room).wgt);
    const auxOn = wgt.filter((room) => attrs(room.state).auxiliary_heat);
    const auxWait = wgt.filter((room) => upcomingOf(room.state).aux_on || upcomingOf(room.state).aux_verdict);

    const heatIn = [
      released
        ? { kind: "no", q: d.releaseQ, a: d.releaseYes({ since: heatSwitch ? sinceText(hass, new Date(heatSwitch.last_changed)) : "–" }) }
        : { kind: "yes", q: d.releaseQ, a: d.releaseNo({ reason: reason ? reason({ outdoor: deg(hass, hub.outdoor_temperature), limit: deg(hass, setting(m.hub, "heat_release_below")), forecast: "", coolLimit: "" }) : "" }), short: d.releaseShort },
    ];
    if (released && today !== null) {
      const low = below.length && today < 12;
      heatIn.push(low
        ? { kind: "yes", q: d.runtimeQ, a: d.runtimeLow({ hours: hoursText(hass, today), nightZero: nightHours !== null && nightHours < 0.1 }), short: d.runtimeShort }
        : { kind: "no", q: d.runtimeQ, a: d.runtimeOk({ hours: hoursText(hass, today) }) });
    }
    if (wgt.length) {
      heatIn.push(auxOn.length
        ? { kind: "no", q: d.auxHelpQ, a: d.auxHelpOn({ n: auxOn.length, names: auxOn.map((r) => r.name).join(", ") }) }
        : auxWait.length
          ? { kind: "wait", q: d.auxHelpQ, a: d.auxHelpWait({ names: auxWait.map((r) => r.name).join(", ") }) }
          : { kind: below.length ? "part" : "no", q: d.auxHelpQ, a: d.auxHelpNone });
    }

    const open = m.rooms.filter((room) => attrs(room.state).window_open);
    const bypass = source(hass, m.hub, "bypass") || m.unit.bypass_state;
    const recovery = numberOf(m.own.heat_recovery);
    const fanText = (say(hass).fan[hub.fan_reason] || say(hass).fan.normal)({ level: hub.fan_level, room: hub.fan_requested_by });
    const heatOut = [
      open.length ? { kind: "yes", q: d.windowsQ, a: d.windowsOpen({ names: open.map((r) => r.name).join(", ") }), short: d.windowsShort } : { kind: "no", q: d.windowsQ, a: d.windowsClosed },
      !bypass ? { kind: "unknown", q: d.recoveryQ, a: d.recoveryUnknown }
        : bypass.state === "closed" ? { kind: "no", q: d.recoveryQ, a: d.recoveryClosed({ recovery: recovery !== null ? `${num(hass, recovery, 0)} %` : "" }) }
          : { kind: "yes", q: d.recoveryQ, a: d.recoveryOpen, short: d.recoveryShort },
      { kind: "no", q: d.fanQ, a: d.fanA({ text: fanText }) },
    ];

    const counts = {};
    for (const room of m.rooms) {
      const v = setting(room.state, "target_normal");
      if (v != null) (counts[v] = counts[v] || []).push(room.name);
    }
    const ordered = Object.entries(counts).sort((x, y) => y[1].length - x[1].length);
    const targetsText = ordered.length <= 1
      ? deg(hass, ordered[0]?.[0])
      : `${ordered.slice(1).map(([v, names]) => `${names.join(", ")} ${deg(hass, Number(v))}`).join(", ")}, ${d.otherwise(deg(hass, Number(ordered[0][0])))}`;
    const setback = m.own.night_setback;
    const holiday = m.own.holiday;
    const goals = [
      { kind: "no", q: d.targetsQ, a: targetsText },
      setback?.state === "on"
        ? { kind: "part", q: d.setbackQ, a: d.setbackOn({ start: setting(m.hub, "night_start"), end: setting(m.hub, "night_end") }) }
        : { kind: "no", q: d.setbackQ, a: d.setbackOff },
      holiday?.state === "on" ? { kind: "yes", q: d.holidayQ, a: d.holidayOn, short: d.holidayShort } : { kind: "no", q: d.holidayQ, a: d.holidayOff },
    ];
    return [
      { title: w.heatIn, items: heatIn },
      { title: w.heatOut, items: heatOut },
      { title: w.goals, items: goals },
    ];
  }

  _warm(hass, m) {
    const w = words(hass);
    const d = dx(hass);
    const hub = attrs(m.hub);
    const compressor = source(hass, m.hub, "compressor");
    const heating = hub.mode === "heating" && compressor && RUNNING(compressor.state);
    const auxOn = m.rooms.filter((room) => attrs(room.state).auxiliary_heat);
    const boosted = m.rooms.filter((room) => attrs(room.state).reason_code === "surplus");
    const excess = thresholdsOf(m.hub).fan_heat_cap?.value;
    const coolSwitch = source(hass, m.hub, "cool_release");
    const reason = say(hass).reason[hub.reason_code];
    return [
      { title: w.heatingQ, items: [
        heating ? { kind: "yes", q: d.heatingQ, a: d.heatingYes({ supply: deg(hass, numberOf(source(hass, m.hub, "supply_air"))) }), short: d.heatingShort } : { kind: "no", q: d.heatingQ, a: d.heatingNo },
        auxOn.length ? { kind: "yes", q: d.auxRunQ, a: auxOn.map((r) => r.name).join(", "), short: d.auxRunShort } : { kind: "no", q: d.auxRunQ, a: d.auxRunNo },
        boosted.length ? { kind: "yes", q: d.boostQ, a: d.boostYes({ boost: kelvin(hass, setting(m.hub, "surplus_target_boost") ?? 1) }), short: d.boostShort } : { kind: "no", q: d.boostQ, a: d.auxRunNo },
      ] },
      { title: w.removedQ, items: [
        excess !== undefined && excess > 0 ? { kind: "yes", q: d.outsideQ, a: d.outsideYes({ outdoor: deg(hass, hub.outdoor_temperature), excess: kelvin(hass, excess) }), short: d.outsideShort } : { kind: "no", q: d.outsideQ, a: d.outsideNo({ outdoor: deg(hass, hub.outdoor_temperature) }) },
        hub.mode !== "cooling" ? { kind: "part", q: d.coolingQ, a: d.coolingOff }
          : coolSwitch?.state === "on" ? { kind: "no", q: d.coolingQ, a: d.coolingOn }
            : { kind: "yes", q: d.coolingQ, a: d.coolingWaits({ reason: reason ? reason({ coolLimit: deg(hass, setting(m.hub, "cool_release_above")) }) : "" }) },
        { kind: "unknown", q: d.otherQ, a: d.otherA },
      ] },
    ];
  }

  _balance(hass) {
    const w = words(hass);
    if (!this._data) return "";
    const days = [];
    const today = startOfToday();
    for (let i = 6; i >= 0; i -= 1) {
      const start = new Date(today.getTime() - i * 86400000);
      const end = i === 0 ? new Date() : new Date(start.getTime() + 86400000);
      const hours = this._data.compressor.length ? hoursIn(this._data.compressor, start, end, RUNNING) : 0;
      const stat = this._data.extract.find((row) => dayLabel(hass, row.start) === dayLabel(hass, start));
      days.push({ label: dayLabel(hass, start), hours, extract: stat?.mean ?? null });
    }
    return `<div style="display:flex;flex-direction:column;gap:10px">
      <div class="split"><span class="eyebrow">${esc(w.balance)}</span></div>
      <div class="week">${days.map((x) => `<div class="col"><span class="mono muted">${esc(x.extract === null ? "–" : deg(hass, x.extract))}</span><div class="well"><span style="height:${Math.round((x.hours / 24) * 100)}%"></span></div><span class="muted">${esc(x.label)}</span><span class="mono">${esc(hoursText(hass, x.hours))}</span></div>`).join("")}</div>
      <span class="small muted">${esc(w.balanceNote)}</span></div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Chronicle

class ChronicleCard extends SccCard {
  async fetch(hass) {
    const m = model(hass);
    if (!m.hub) return null;
    const s = attrs(m.hub).sources || {};
    const contacts = m.rooms.flatMap((room) => (attrs(room.state).sources || {}).contacts || []);
    const own = Object.values(m.own).map((state) => state.entity_id).filter((id) => /^(switch|select|number)\./.test(id));
    const ids = [m.hub.entity_id, ...m.rooms.map((r) => r.id), s.compressor, ...contacts, ...own].filter(Boolean);
    return { events: await logbook(hass, ids, new Date(Date.now() - 24 * 3600000)), contacts, compressor: s.compressor, decisions: new Set([m.hub.entity_id, ...m.rooms.map((r) => r.id)]) };
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const legend = [["blue", w.byController], ["orange", w.byDevice], ["grey", w.byOutside]];
    const head = `${header(hass, w.chronicle, w.chronicleLead, [])}
      <div class="row" style="gap:8px">${legend.map(([tone, text]) => `<span class="pill grey" style="gap:8px"><span class="dot ${tone}"></span>${esc(text)}</span>`).join("")}</div>`;
    if (!this._data) return `${head}<p class="empty">${esc(w.loading)}</p>`;
    const { events, contacts, compressor, decisions } = this._data;
    const rows = [];
    for (const ev of events) {
      const when = new Date(ev.when * 1000);
      const stateObj = hass.states[ev.entity_id];
      const name = ev.name || stateObj?.attributes.friendly_name || ev.entity_id;
      if (decisions.has(ev.entity_id) || ev.domain === DOMAIN) {
        if (!ev.message || /^(changed to|wurde)/.test(ev.message)) continue;
        const room = m.rooms.find((r) => r.id === ev.entity_id);
        rows.push({ when, tone: "blue", what: room ? room.name : w.controller, why: ev.message });
      } else if (ev.entity_id === compressor) {
        const shown = stateObj && hass.formatEntityState ? hass.formatEntityState(stateObj, ev.state) : ev.state;
        rows.push({ when, tone: "orange", what: `${w.heatPump}: ${shown}`, why: "" });
      } else if (contacts.includes(ev.entity_id)) {
        const shown = stateObj && hass.formatEntityState ? hass.formatEntityState(stateObj, ev.state) : ev.state;
        rows.push({ when, tone: "grey", what: `${name}: ${shown}`, why: "" });
      } else if (ev.state !== undefined) {
        const shown = stateObj && hass.formatEntityState ? hass.formatEntityState(stateObj, ev.state) : ev.state;
        rows.push({ when, tone: ev.context_user_id ? "grey" : "blue", what: `${name}: ${shown}`, why: "" });
      }
    }
    rows.sort((x, y) => y.when - x.when);
    const list = rows.slice(0, 60).map((r) => `<li><span class="mono small muted" style="padding-top:2px">${esc(sinceText(hass, r.when))}</span><span class="dot ${r.tone}"></span><div style="display:flex;flex-direction:column;gap:2px"><span style="font-size:15px;font-weight:500">${esc(r.what)}</span>${r.why ? `<span class="small muted" style="line-height:1.45">${esc(r.why)}</span>` : ""}</div></li>`).join("");
    return `${head}<ol class="events">${list || `<li class="empty">–</li>`}</ol>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// The unit itself

class DeviceCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    return [m.hub?.entity_id, m.own.missing_inputs?.entity_id, m.own.heat_recovery?.entity_id, ...Object.values(m.unit).map((s) => s.entity_id)].filter(Boolean);
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const u = m.unit;
    const val = (type) => numberOf(u[type]);
    const fault = u.error_message?.state;
    const faultOk = fault === undefined || ["0", "", "unknown", "unavailable"].includes(fault);
    const operation = source(hass, m.hub, "operation_mode");
    const manual = !operation || operation.state === "manual";
    const supplyFlow = val("current_supply_air_flow");
    const exhaustFlow = val("current_exhaust_air_flow");
    const balanced = supplyFlow === null || exhaustFlow === null || Math.abs(supplyFlow - exhaustFlow) <= 5;
    const recovery = numberOf(m.own.heat_recovery);
    const bypass = u.bypass_state?.state;
    const filter = val("device_filter_remaining");
    const stuck = attrs(m.own.missing_inputs).stuck_writes || [];
    const missing = attrs(m.hub).failed_inputs || [];
    const checks = [
      [faultOk, w.fault, faultOk ? w.noFault : fault, ""],
      [manual, w.operation, operation ? (hass.formatEntityState ? hass.formatEntityState(operation) : operation.state) : "–", manual ? w.mustBeManual : w.notManual],
      [balanced, w.fans, supplyFlow !== null ? `${num(hass, supplyFlow, 0)} % / ${num(hass, exhaustFlow, 0)} %` : "–", u.current_supply_air_rpm ? `${num(hass, val("current_supply_air_rpm"), 0)} / ${num(hass, val("current_exhaust_air_rpm"), 0)} U/min` : ""],
      [true, w.recovery, recovery !== null ? `${num(hass, recovery, 0)} %` : "–", bypass ? (bypass === "closed" ? w.bypassClosed : w.bypassOpen) : ""],
      [filter === null || filter > 14, w.filter, filter !== null ? w.days(num(hass, filter, 0)) : "–", w.remaining],
      [!stuck.length && !missing.length, w.controller, stuck.length ? w.notTaken(stuck.length) : w.allTaken, missing.length ? w.missingInputs(missing.length) : w.allInputs],
    ];
    const ok = checks.every(([pass]) => pass);
    const tiles = checks.map(([pass, label, value, note]) => `<div class="tile"><span class="row small muted" style="gap:8px"><span class="dot ${pass ? "blue" : "orange"}" style="width:8px;height:8px"></span>${esc(label)}</span><span class="value">${esc(value)}</span>${note ? `<span class="note">${esc(note)}</span>` : ""}</div>`).join("");

    const st = w.stages;
    const stage = (name, type, tone, sensor) => {
      const v = val(type);
      return v === null ? "" : `<div class="stage ${tone}"><span class="small muted">${esc(name)}</span><span class="t">${esc(deg(hass, v))}</span><span class="small muted mono">${esc(sensor)}</span></div>`;
    };
    const chain = (items) => items.filter(Boolean).join(`<span class="arrow">${ICONS.arrow}</span>`);
    const t10 = val("temperature_t10_outdoor");
    const t3 = val("temperature_t3_before_reheater");
    const t4 = val("temperature_t4_after_reheater");
    const t5 = val("temperature_t5_exhaust_air");
    const t6 = val("temperature_t6_in_heat_exchanger");
    const t8 = val("temperature_t8_condenser");
    const t2 = val("temperature_t2_after_preheating_coil");
    const wt = t3 !== null && (t2 ?? t10) !== null ? t3 - (t2 ?? t10) : null;
    const hp = t4 !== null && t3 !== null && t4 - t3 > 1 ? t4 - t3 : null;
    const fresh = chain([
      stage(st.outdoor, "temperature_t10_outdoor", "cold", "T10"),
      stage(st.t2, "temperature_t2_after_preheating_coil", "cold", "T2"),
      stage(st.t3, "temperature_t3_before_reheater", "", "T3"),
      t8 !== null && hp ? stage(st.t8, "temperature_t8_condenser", "hot", "T8") : "",
      stage(st.t4, "temperature_t4_after_reheater", t4 !== null && t4 > 30 ? "hot" : "warm", "T4"),
    ]);
    const exhaust = chain([
      stage(st.t5, "temperature_t5_exhaust_air", "warm", "T5"),
      stage(st.t6, "temperature_t6_in_heat_exchanger", "", "T6"),
      stage(st.t7, "temperature_t7_evaporator", "cold", "T7"),
    ]);
    void t5;
    void t6;

    return `${header(hass, w.device, ok ? w.deviceOk : w.deviceNotOk, [])}
      <div class="grid" style="--min:138px">${tiles}</div>
      ${fresh ? `<div style="display:flex;flex-direction:column;gap:16px">
        <div class="split"><span class="eyebrow">${esc(w.airPath)}</span><span class="small muted">${esc(w.airPathLead)}</span></div>
        <div style="display:flex;flex-direction:column;gap:8px"><span style="font-weight:500">${esc(w.freshAir)}</span><div class="path">${fresh}</div>${wt !== null ? `<span class="small muted">${esc(w.gainNote(kelvin(hass, wt), hp ? kelvin(hass, hp) : ""))}</span>` : ""}</div>
        ${exhaust ? `<div style="display:flex;flex-direction:column;gap:8px"><span style="font-weight:500">${esc(w.exhaustAir)}</span><div class="path">${exhaust}</div><span class="small muted">${esc(w.evaporatorNote)}</span></div>` : ""}
      </div>` : ""}`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Air, for ventilation

class AirCard extends SccCard {
  watched(hass) {
    const m = model(hass);
    const ids = m.rooms.flatMap((room) => {
      const s = attrs(room.state).sources || {};
      return [s.co2, s.humidity];
    });
    return [m.hub?.entity_id, ...ids].filter(Boolean);
  }

  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const hub = attrs(m.hub);
    const rows = m.rooms.map((room) => {
      const s = attrs(room.state).sources || {};
      const co2 = numberOf(s.co2 ? hass.states[s.co2] : null);
      const hum = numberOf(s.humidity ? hass.states[s.humidity] : null);
      return { room, co2, hum, co2Max: setting(room.state, "co2_high"), humMax: setting(room.state, "humidity_high") };
    }).filter((r) => r.co2 !== null || r.hum !== null);
    const fan = (say(hass).fan[hub.fan_reason] || say(hass).fan.normal)({ level: hub.fan_level, room: hub.fan_requested_by });
    const cell = (v, max, unit, digits) => {
      if (v === null) return `<td class="muted">–</td>`;
      const ratio = max ? v / max : 0;
      return `<td><span class="mono ${ratio >= 1 ? "orange" : ""}" style="font-weight:500">${esc(num(hass, v, digits))} ${esc(unit)}</span><div class="track ${ratio >= 0.85 ? "near" : ""}" style="margin-top:6px;max-width:160px"><span style="width:${Math.round(Math.min(1, ratio) * 100)}%"></span></div></td>`;
    };
    return `<div class="split"><span class="title">${esc(w.air)}</span><span class="lead">${esc(w.airLead)}</span></div>
      <div class="row" style="gap:10px"><span class="eyebrow">${esc(w.fanStage)}</span><span style="font-weight:500">${esc(fan)}</span></div>
      ${rows.length ? `<div class="scroll"><table><thead><tr><th>${esc(w.room)}</th><th>${esc(w.co2)}</th><th>${esc(w.humidity)}</th></tr></thead><tbody>${rows.map((r) => `<tr><th scope="row">${link(roomView(r.room), esc(r.room.name))}</th>${cell(r.co2, r.co2Max, "ppm", 0)}${cell(r.hum, r.humMax, "%", 0)}</tr>`).join("")}</tbody></table></div>` : `<p class="empty">${esc(w.noAirSensors)}</p>`}`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Cooling

class CoolingCard extends SccCard {
  content(hass, m) {
    if (!m.hub) return null;
    const w = words(hass);
    const hub = attrs(m.hub);
    const coolSwitch = source(hass, m.hub, "cool_release");
    const on = coolSwitch ? coolSwitch.state === "on" : !!hub.cool_release;
    const reason = say(hass).reason[hub.reason_code];
    const text = reason ? reason({ coolLimit: deg(hass, setting(m.hub, "cool_release_above")), outdoor: deg(hass, hub.outdoor_temperature), limit: "", forecast: "" }) : "";
    const release = levers(hass, m.hub, ["cool_release_on", "cool_release_off", "surplus_on", "release_lockout_ends"], 3).map((l) => l.html).join("");
    const protect = levers(hass, m.hub, ["fan_heat_cap", "fan_off", "night_starts", "night_ends"], 3).map((l) => l.html).join("");
    const nightCooling = hub.fan_reason === "night_cooling";
    return `<div class="split"><span class="title">${esc(w.coolingTitle)}</span>${pill(on ? w.free : w.locked, on ? "blue" : "grey")}</div>
      <p class="lead">${esc(text)}</p>
      <div class="grid" style="--min:260px;gap:20px">
        <div style="display:flex;flex-direction:column;gap:14px"><span class="eyebrow">${esc(w.howClose)}</span>${release}</div>
        <div style="display:flex;flex-direction:column;gap:14px"><span class="eyebrow">${esc(w.nightCooling)} · ${esc(w.heatProtection)}</span>
          <span class="row" style="gap:8px">${pill(nightCooling ? w.on : w.off, nightCooling ? "blue" : "grey")}<span class="small muted">${esc((say(hass).fan[hub.fan_reason] || say(hass).fan.normal)({ level: hub.fan_level }))}</span></span>
          ${protect}
        </div>
      </div>`;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Ways onward

class LinksCard extends SccCard {
  content(hass) {
    const items = (this._config.links || []).map(([view, label]) => `<a href="${esc(viewPath(view))}" data-view="${esc(view)}">${esc(label)}</a>`).join("");
    return `<div class="links">${items}</div>`;
  }

  getCardSize() {
    return 1;
  }
}

////////////////////////////////////////////////////////////////////////////////

const CARDS = {
  "schwoerer-alerts-card": AlertsCard,
  "schwoerer-health-card": HealthCard,
  "schwoerer-energy-card": EnergyCard,
  "schwoerer-heat-pump-card": HeatPumpCard,
  "schwoerer-aux-card": AuxCard,
  "schwoerer-room-card": RoomCard,
  "schwoerer-house-card": HouseCard,
  "schwoerer-chronicle-card": ChronicleCard,
  "schwoerer-device-card": DeviceCard,
  "schwoerer-air-card": AirCard,
  "schwoerer-cooling-card": CoolingCard,
  "schwoerer-links-card": LinksCard,
};

function registerCards(registry) {
  for (const [tag, element] of Object.entries(CARDS)) {
    if (!registry.get(tag)) registry.define(tag, class extends element {});
  }
}

window.customCards = window.customCards || [];
for (const tag of Object.keys(CARDS)) {
  if (!window.customCards.some((card) => card.type === tag)) {
    window.customCards.push({ type: tag, name: `Schwörer ${tag.replace("schwoerer-", "").replace("-card", "")}`, description: "Schwörer Climate Control" });
  }
}

// Same reasoning as the strategy: keep registering into whatever registry the
// frontend ends up using until its own <home-assistant> element is in it.
const CARDS_SETTLE_MS = 60000;
const cardsStarted = Date.now();
(function registerCardsUntilSettled() {
  registerCards(window.customElements);
  if (!window.customElements.get("home-assistant") && Date.now() - cardsStarted < CARDS_SETTLE_MS) {
    setTimeout(registerCardsUntilSettled, 25);
  }
})();
