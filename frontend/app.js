/**
 * MathOCR browser client by Bouronikos Christos <chrisbouronikos@gmail.com>.
 * Support the project at https://paypal.me/christosbouronikos.
 *
 * Plain JavaScript, no build step: the same files run from GitHub Pages, from
 * the local FastAPI service, and inside the packaged desktop application.
 * All text lives in the translations table so the interface is fully
 * bilingual (English / Greek).
 */

"use strict";

const APP_VERSION = "1.0.0";
const MAX_FILE_BYTES = 25 * 1024 * 1024;
const MAX_FILES = 12;
const RELEASES_URL = "https://github.com/ChristosBouronikos/MathOCR/releases/latest";
const AUTHOR_SUFFIX = "by Bouronikos Christos"; // every exported file ends with this
const ENGINE_SHORT_NAMES = {
  "pix2text-mfr": "Pix2Text MFR",
  pix2tex: "pix2tex",
  "rapid-latex": "RapidLaTeX",
};

const translations = {
  en: {
    pageTitle: "MathOCR by Bouronikos Christos",
    brandBy: "by Bouronikos Christos",
    refreshPage: "Refresh",
    updateTitle: "A new version is available",
    updateDetail: "MathOCR {{latest}} is available — you have {{current}}.",
    updateNotes: "Release notes ↗",
    updateNow: "Update now",
    updateDownload: "Download ↗",
    updateStartedWin: "Installer launched. MathOCR will now close to finish updating.",
    updateStartedMac: "Update downloaded to your Downloads folder. Drag MathOCR into Applications to replace the old version, then reopen it.",
    updateFailed: "The update could not be downloaded — try again or download it from GitHub.",
    serviceChecking: "Checking engine…",
    serviceReady: "Local engine ready",
    serviceNoPandoc: "OCR ready · Pandoc missing",
    serviceOffline: "Engine offline",
    eyebrow: "LOCAL MATHEMATICS OCR",
    introTitle: "Images and PDFs into editable equations.",
    introCopy: "Drop a file, review the LaTeX, export editable Word equations. Everything runs on your computer.",
    engineBannerTitle: "The local engine is not running.",
    engineBannerCopy: "Recognition happens on your computer, so MathOCR needs its engine.",
    engineBannerAction: "Get the desktop app",
    dropFiles: "Drop images or PDFs here",
    browseFiles: "click to browse, or paste a screenshot (Ctrl+V) · PNG, JPG, WEBP, TIFF, PDF",
    inputType: "What do you want to recognize?",
    modeDocument: "All text + math (whole document)",
    modeMixed: "Only the math inside a page of text",
    modeFormula: "Only one equation (cropped image)",
    mathEngine: "Math engine",
    engineBest: "Best — cross-check all (recommended)",
    enginePix2text: "Pix2Text MFR-1.5",
    enginePix2tex: "pix2tex (LaTeX-OCR)",
    engineRapid: "RapidLaTeXOCR",
    docReader: "Text reader (document mode)",
    docLayout: "Greek + English (Tesseract)",
    docNougat: "Nougat — English papers",
    docNougatUnavailable: "Nougat — download it below first",
    pageLimit: "PDF page limit",
    recognize: "Recognize mathematics",
    engineAddress: "Advanced: engine address",
    checkConnection: "Check connection",
    connectionInitial: "Start the local engine to enable recognition and Word export.",
    filesStayLocal: "Files are sent only to the MathOCR engine on this computer.",
    installPandoc: "OCR works, but Pandoc is required for Word export.",
    startEngine: "Start the local engine to enable recognition and Word export.",
    readingMath: "Reading mathematics…",
    processingNote: "Processing can take several minutes depending on file size and model availability.",
    reconstructedDocument: "Reconstructed document",
    documentHint: "Edit the text and math below, then export the whole document to Word.",
    copyDocument: "Copy text",
    downloadDocWord: "Download document (Word)",
    editableDocument: "Editable document text and LaTeX",
    documentCopied: "Document text copied",
    documentTitle: "MathOCR document",
    recognizedEquations: "Recognized equations",
    resultsOne: "1 equation found. Edit the LaTeX and the preview updates live.",
    resultsMany: "{{count}} equations found. Edit the LaTeX and the preview updates live.",
    noEquationsDetected: "No equations were detected. Try a clearer image, or the “One cropped equation” mode.",
    reviewReminder: "OCR can make convincing mistakes — always compare with the source.",
    copyAll: "Copy all LaTeX",
    downloadTex: "Download .tex",
    downloadWord: "Download Word",
    page: "Page",
    confidence: "confidence",
    alternativeReadings: "Other engines read:",
    editableLatex: "Editable LaTeX",
    renderedPreview: "Rendered equation preview",
    copyLatex: "Copy",
    remove: "Remove",
    latexCopied: "LaTeX copied",
    allLatexCopied: "All LaTeX copied",
    clipboardBlocked: "Clipboard access was blocked",
    nothingToExport: "There are no equations to export",
    buildingWord: "Building Word…",
    wordFailed: "Word export failed",
    wordCreated: "Editable Word document created",
    texTitle: "MathOCR equations",
    unsupportedFile: "{{name}}: unsupported file type",
    fileTooLarge: "{{name}}: file is larger than 25 MB",
    maximumFiles: "A maximum of {{count}} files is allowed",
    removeFile: "Remove file",
    pastedImage: "Pasted image added",
    recognitionFailed: "Recognition failed",
    recognitionHttpFailed: "Recognition failed (HTTP {{status}})",
    foundOne: "Found 1 equation",
    foundMany: "Found {{count}} equations",
    storageTitle: "Models on this computer",
    storageCopy: "Recognition models are downloaded once and stored locally. Delete them anytime to free disk space; they download again when needed.",
    storageTotal: "Total space used",
    storagePath: "Storage folder",
    storageNotInstalled: "not installed",
    storageEmpty: "not downloaded",
    storageReady: "ready",
    storageLoaded: "in memory",
    storageOptional: "optional · English documents",
    storageWeightsMissing: "installed · weights not downloaded",
    downloadModel: "Download",
    installingNougat: "Installing Nougat… downloads ~1.4 GB, several minutes",
    nougatReady: "Nougat is ready — select it in the document reader menu",
    nougatInstallFailed: "Nougat installation failed",
    nougatNeedsSource: "Available when running MathOCR from source",
    role_math: "math",
    role_text: "text",
    role_optional: "optional",
    downloadModels: "Download all models now",
    downloadingModels: "Downloading models… this can take several minutes",
    modelsReady: "Models are ready ({{size}})",
    modelsDownloadFailed: "Model download failed — check the connection",
    deleteAllModels: "Delete all models",
    deleteModel: "Delete",
    confirmDelete: "Click again to confirm",
    modelsDeleted: "Freed {{size}} of disk space",
    modelsDeleteFailed: "Some files could not be deleted — close the app and delete the folder manually",
    storageUnavailable: "Storage information needs the local engine.",
    privateTitle: "Private by design.",
    privateCopy: "Files are processed only by the MathOCR engine running on this computer and never leave it.",
    footerTagline: "Local mathematics recognition with editable output.",
    footerProject: "Project",
    footerSource: "Source code",
    footerDownloads: "Downloads",
    footerReportBug: "Report a bug",
    footerAuthor: "Author",
    footerGithub: "GitHub profile",
    footerDonate: "Support on PayPal ♥",
    footerLicense: "MIT License",
    footerMadeWith: "made for students, teachers, and researchers",
  },
  el: {
    pageTitle: "MathOCR από τον Χρήστο Μπουρονίκο",
    brandBy: "από τον Χρήστο Μπουρονίκο",
    refreshPage: "Ανανέωση",
    updateTitle: "Διαθέσιμη νέα έκδοση",
    updateDetail: "Η έκδοση MathOCR {{latest}} είναι διαθέσιμη — έχετε την {{current}}.",
    updateNotes: "Σημειώσεις έκδοσης ↗",
    updateNow: "Ενημέρωση τώρα",
    updateDownload: "Λήψη ↗",
    updateStartedWin: "Ο εγκαταστάτης ξεκίνησε. Το MathOCR θα κλείσει τώρα για να ολοκληρωθεί η ενημέρωση.",
    updateStartedMac: "Η ενημέρωση κατέβηκε στον φάκελο Λήψεις. Σύρετε το MathOCR στις Εφαρμογές για να αντικαταστήσετε την παλιά έκδοση και ανοίξτε το ξανά.",
    updateFailed: "Η ενημέρωση δεν κατέβηκε — δοκιμάστε ξανά ή κατεβάστε την από το GitHub.",
    serviceChecking: "Έλεγχος μηχανής…",
    serviceReady: "Η τοπική μηχανή είναι έτοιμη",
    serviceNoPandoc: "OCR έτοιμο · λείπει το Pandoc",
    serviceOffline: "Μηχανή εκτός λειτουργίας",
    eyebrow: "ΤΟΠΙΚΗ ΑΝΑΓΝΩΡΙΣΗ ΜΑΘΗΜΑΤΙΚΩΝ",
    introTitle: "Εικόνες και PDF σε επεξεργάσιμες εξισώσεις.",
    introCopy: "Αφήστε ένα αρχείο, ελέγξτε το LaTeX, εξαγάγετε επεξεργάσιμες εξισώσεις Word. Όλα εκτελούνται στον υπολογιστή σας.",
    engineBannerTitle: "Η τοπική μηχανή δεν εκτελείται.",
    engineBannerCopy: "Η αναγνώριση γίνεται στον υπολογιστή σας, οπότε το MathOCR χρειάζεται τη μηχανή του.",
    engineBannerAction: "Κατεβάστε την εφαρμογή",
    dropFiles: "Σύρετε εδώ εικόνες ή PDF",
    browseFiles: "κλικ για επιλογή, ή επικόλληση στιγμιότυπου (Ctrl+V) · PNG, JPG, WEBP, TIFF, PDF",
    inputType: "Τι θέλετε να αναγνωρίσετε;",
    modeDocument: "Όλο το κείμενο + μαθηματικά (ολόκληρο έγγραφο)",
    modeMixed: "Μόνο τα μαθηματικά μέσα σε σελίδα με κείμενο",
    modeFormula: "Μόνο μία εξίσωση (κομμένη εικόνα)",
    mathEngine: "Μηχανή μαθηματικών",
    engineBest: "Βέλτιστη — διασταύρωση όλων (προτείνεται)",
    enginePix2text: "Pix2Text MFR-1.5",
    enginePix2tex: "pix2tex (LaTeX-OCR)",
    engineRapid: "RapidLaTeXOCR",
    docReader: "Ανάγνωση κειμένου (λειτουργία εγγράφου)",
    docLayout: "Ελληνικά + Αγγλικά (Tesseract)",
    docNougat: "Nougat — αγγλικές εργασίες",
    docNougatUnavailable: "Nougat — κατεβάστε το πρώτα πιο κάτω",
    pageLimit: "Όριο σελίδων PDF",
    recognize: "Αναγνώριση μαθηματικών",
    engineAddress: "Για προχωρημένους: διεύθυνση μηχανής",
    checkConnection: "Έλεγχος σύνδεσης",
    connectionInitial: "Εκκινήστε την τοπική μηχανή για αναγνώριση και εξαγωγή Word.",
    filesStayLocal: "Τα αρχεία αποστέλλονται μόνο στη μηχανή MathOCR αυτού του υπολογιστή.",
    installPandoc: "Το OCR λειτουργεί, αλλά για εξαγωγή Word απαιτείται το Pandoc.",
    startEngine: "Εκκινήστε την τοπική μηχανή για αναγνώριση και εξαγωγή Word.",
    readingMath: "Ανάγνωση μαθηματικών…",
    processingNote: "Η επεξεργασία μπορεί να διαρκέσει αρκετά λεπτά ανάλογα με το μέγεθος του αρχείου και τη διαθεσιμότητα των μοντέλων.",
    reconstructedDocument: "Ανακατασκευασμένο έγγραφο",
    documentHint: "Επεξεργαστείτε το κείμενο και τα μαθηματικά και εξαγάγετε όλο το έγγραφο σε Word.",
    copyDocument: "Αντιγραφή κειμένου",
    downloadDocWord: "Λήψη εγγράφου (Word)",
    editableDocument: "Επεξεργάσιμο κείμενο εγγράφου και LaTeX",
    documentCopied: "Το κείμενο του εγγράφου αντιγράφηκε",
    documentTitle: "Έγγραφο MathOCR",
    recognizedEquations: "Αναγνωρισμένες εξισώσεις",
    resultsOne: "Βρέθηκε 1 εξίσωση. Επεξεργαστείτε το LaTeX και η προεπισκόπηση ενημερώνεται άμεσα.",
    resultsMany: "Βρέθηκαν {{count}} εξισώσεις. Επεξεργαστείτε το LaTeX και η προεπισκόπηση ενημερώνεται άμεσα.",
    noEquationsDetected: "Δεν εντοπίστηκαν εξισώσεις. Δοκιμάστε καθαρότερη εικόνα ή τη λειτουργία «Μία εξίσωση».",
    reviewReminder: "Το OCR μπορεί να κάνει πειστικά λάθη — συγκρίνετε πάντα με το πρωτότυπο.",
    copyAll: "Αντιγραφή όλου του LaTeX",
    downloadTex: "Λήψη .tex",
    downloadWord: "Λήψη Word",
    page: "Σελίδα",
    confidence: "βεβαιότητα",
    alternativeReadings: "Άλλες μηχανές διάβασαν:",
    editableLatex: "Επεξεργάσιμο LaTeX",
    renderedPreview: "Προεπισκόπηση εξίσωσης",
    copyLatex: "Αντιγραφή",
    remove: "Αφαίρεση",
    latexCopied: "Το LaTeX αντιγράφηκε",
    allLatexCopied: "Όλο το LaTeX αντιγράφηκε",
    clipboardBlocked: "Η πρόσβαση στο πρόχειρο αποκλείστηκε",
    nothingToExport: "Δεν υπάρχουν εξισώσεις για εξαγωγή",
    buildingWord: "Δημιουργία Word…",
    wordFailed: "Η εξαγωγή Word απέτυχε",
    wordCreated: "Το επεξεργάσιμο έγγραφο Word δημιουργήθηκε",
    texTitle: "Εξισώσεις MathOCR",
    unsupportedFile: "{{name}}: μη υποστηριζόμενος τύπος αρχείου",
    fileTooLarge: "{{name}}: το αρχείο ξεπερνά τα 25 MB",
    maximumFiles: "Επιτρέπονται έως {{count}} αρχεία",
    removeFile: "Αφαίρεση αρχείου",
    pastedImage: "Η επικολλημένη εικόνα προστέθηκε",
    recognitionFailed: "Η αναγνώριση απέτυχε",
    recognitionHttpFailed: "Η αναγνώριση απέτυχε (HTTP {{status}})",
    foundOne: "Βρέθηκε 1 εξίσωση",
    foundMany: "Βρέθηκαν {{count}} εξισώσεις",
    storageTitle: "Μοντέλα σε αυτόν τον υπολογιστή",
    storageCopy: "Τα μοντέλα αναγνώρισης κατεβαίνουν μία φορά και αποθηκεύονται τοπικά. Μπορείτε να τα διαγράψετε όποτε θέλετε για να ελευθερώσετε χώρο· θα κατέβουν ξανά όταν χρειαστούν.",
    storageTotal: "Συνολικός χώρος",
    storagePath: "Φάκελος αποθήκευσης",
    storageNotInstalled: "μη εγκατεστημένη",
    storageEmpty: "δεν έχει κατέβει",
    storageReady: "έτοιμο",
    storageLoaded: "στη μνήμη",
    storageOptional: "προαιρετικό · αγγλικά έγγραφα",
    storageWeightsMissing: "εγκατεστημένο · δεν έχουν κατέβει τα βάρη",
    downloadModel: "Λήψη",
    installingNougat: "Εγκατάσταση Nougat… κατεβάζει ~1,4 GB, μερικά λεπτά",
    nougatReady: "Το Nougat είναι έτοιμο — επιλέξτε το στο μενού ανάγνωσης εγγράφου",
    nougatInstallFailed: "Η εγκατάσταση του Nougat απέτυχε",
    nougatNeedsSource: "Διαθέσιμο όταν το MathOCR εκτελείται από τον πηγαίο κώδικα",
    role_math: "μαθηματικά",
    role_text: "κείμενο",
    role_optional: "προαιρετικό",
    downloadModels: "Λήψη όλων των μοντέλων τώρα",
    downloadingModels: "Λήψη μοντέλων… μπορεί να διαρκέσει αρκετά λεπτά",
    modelsReady: "Τα μοντέλα είναι έτοιμα ({{size}})",
    modelsDownloadFailed: "Η λήψη των μοντέλων απέτυχε — ελέγξτε τη σύνδεση",
    deleteAllModels: "Διαγραφή όλων των μοντέλων",
    deleteModel: "Διαγραφή",
    confirmDelete: "Πατήστε ξανά για επιβεβαίωση",
    modelsDeleted: "Ελευθερώθηκαν {{size}} χώρου",
    modelsDeleteFailed: "Κάποια αρχεία δεν διαγράφηκαν — κλείστε την εφαρμογή και διαγράψτε τον φάκελο χειροκίνητα",
    storageUnavailable: "Οι πληροφορίες αποθήκευσης απαιτούν την τοπική μηχανή.",
    privateTitle: "Σχεδιασμένο για ιδιωτικότητα.",
    privateCopy: "Τα αρχεία επεξεργάζονται μόνο από τη μηχανή MathOCR αυτού του υπολογιστή και δεν φεύγουν ποτέ από αυτόν.",
    footerTagline: "Τοπική αναγνώριση μαθηματικών με επεξεργάσιμο αποτέλεσμα.",
    footerProject: "Έργο",
    footerSource: "Πηγαίος κώδικας",
    footerDownloads: "Λήψεις",
    footerReportBug: "Αναφορά σφάλματος",
    footerAuthor: "Δημιουργός",
    footerGithub: "Προφίλ GitHub",
    footerDonate: "Υποστήριξη μέσω PayPal ♥",
    footerLicense: "Άδεια MIT",
    footerMadeWith: "φτιαγμένο για μαθητές, εκπαιδευτικούς και ερευνητές",
  },
};

const params = new URLSearchParams(window.location.search);
const isDesktop = params.get("desktop") === "1";
const savedLanguage = localStorage.getItem("mathocr-language");
const initialLanguage = savedLanguage || (navigator.language.toLowerCase().startsWith("el") ? "el" : "en");

const state = {
  files: [],
  results: [],
  documents: [],
  online: false,
  pandoc: false,
  textAvailable: false,
  nougatAvailable: false,
  nougatReady: false,
  nougatInstallable: false,
  busy: false,
  language: initialLanguage,
  storage: null,
  update: null,
};

function t(key, variables = {}) {
  const template = translations[state.language][key] || translations.en[key] || key;
  return Object.entries(variables).reduce(
    (value, [name, replacement]) => value.replaceAll(`{{${name}}}`, String(replacement)),
    template,
  );
}

const elements = {};
for (const id of [
  "apiUrl", "connectionHelp", "copyAllButton", "copyDocButton", "deleteAllModelsButton",
  "downloadModelsButton", "downloadDocWordButton", "downloadTexButton", "downloadWordButton",
  "dropZone", "engineBanner", "engineBannerLink", "advancedSettings", "docEngine", "docEngineField",
  "documentList", "documentSection", "fileInput", "fileList", "footerVersion", "mathEngine",
  "pageLimit", "progressPanel", "recognitionMode", "recognizeButton", "recheckButton", "refreshPageButton",
  "resultList", "resultsSection", "resultsSummary", "servicePill", "serviceText", "storageList",
  "storagePathValue", "storageSection", "storageTotalBytes", "toast",
  "updateBanner", "updateButton", "updateDetail", "updateNotesLink",
]) {
  elements[id] = document.querySelector(`#${id}`);
}

/* ---------- language ---------- */

function applyLanguage(language) {
  state.language = language === "el" ? "el" : "en";
  localStorage.setItem("mathocr-language", state.language);
  document.documentElement.lang = state.language;
  document.title = t("pageTitle");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-language]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.language === state.language));
  });
  updateServiceCopy();
  updateModeOptions();
  renderFiles();
  renderStorage();
  renderUpdateBanner();
  if (!elements.documentSection.hidden) renderDocuments();
  if (!elements.resultsSection.hidden) renderResults(false);
}

/* ---------- helpers ---------- */

function normalizedApiUrl() {
  return elements.apiUrl.value.trim().replace(/\/+$/, "");
}

function humanBytes(bytes) {
  if (!bytes) return "0 MB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

let toastTimer;
function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  toastTimer = setTimeout(() => elements.toast.classList.remove("visible"), 3200);
}

function updateControls() {
  elements.recognizeButton.disabled = !state.online || !state.files.length || state.busy;
  elements.fileInput.disabled = state.busy;
  elements.apiUrl.disabled = state.busy;
}

/* ---------- engine status ---------- */

function updateServiceCopy() {
  if (state.online) {
    elements.serviceText.textContent = state.pandoc ? t("serviceReady") : t("serviceNoPandoc");
    elements.connectionHelp.textContent = state.pandoc ? t("filesStayLocal") : t("installPandoc");
  } else {
    elements.serviceText.textContent = t("serviceOffline");
    elements.connectionHelp.textContent = t("startEngine");
  }
  elements.engineBanner.hidden = state.online || isDesktop;
}

async function checkService() {
  elements.servicePill.className = "service-pill";
  elements.serviceText.textContent = t("serviceChecking");
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/health`, { signal: AbortSignal.timeout(2800) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    state.online = true;
    state.pandoc = Boolean(health.pandoc);
    state.textAvailable = Boolean(health.text_available);
    state.nougatAvailable = Boolean(health.nougat_available);
    state.nougatReady = Boolean(health.nougat_ready);
    state.nougatInstallable = Boolean(health.nougat_installable);
    elements.servicePill.classList.add("online");
    refreshStorage();
    checkUpdate(); // non-blocking: reveal the banner if a newer release exists
  } catch (_error) {
    state.online = false;
    state.pandoc = false;
    state.textAvailable = false;
    state.nougatAvailable = false;
    state.nougatReady = false;
    state.nougatInstallable = false;
    state.storage = null;
    elements.servicePill.classList.add("offline");
    renderStorage();
  }
  updateServiceCopy();
  updateModeOptions();
  updateControls();
}

/* ---------- in-app updates ---------- */

async function checkUpdate() {
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/update/check`, {
      signal: AbortSignal.timeout(9000),
    });
    if (!response.ok) return; // offline or rate-limited: stay quiet
    state.update = await response.json();
  } catch (_error) {
    return; // never let an update check disrupt normal use
  }
  renderUpdateBanner();
}

function renderUpdateBanner() {
  const info = state.update;
  if (!info || !info.update_available) {
    elements.updateBanner.hidden = true;
    return;
  }
  elements.updateBanner.hidden = false;
  elements.updateDetail.textContent = t("updateDetail", {
    latest: info.latest,
    current: info.current,
  });
  elements.updateNotesLink.href = info.notes_url || "#";
  // In the packaged app the button installs in place; from source (or a browser)
  // it becomes a plain link to the releases page.
  elements.updateButton.textContent = info.can_install ? t("updateNow") : t("updateDownload");
}

async function installUpdate() {
  const info = state.update || {};
  if (!info.can_install) {
    window.open(info.notes_url || "https://github.com/ChristosBouronikos/MathOCR/releases/latest", "_blank");
    return;
  }
  elements.updateButton.disabled = true;
  elements.updateButton.textContent = t("downloadingModels");
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/update/install`, { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || t("updateFailed"));
    const message = payload.platform === "darwin" ? t("updateStartedMac") : t("updateStartedWin");
    elements.updateDetail.textContent = message;
    elements.updateButton.hidden = true;
    showToast(message);
  } catch (error) {
    showToast(error.message || t("updateFailed"));
    elements.updateButton.disabled = false;
    elements.updateButton.textContent = t("updateNow");
  }
}

/* ---------- mode + engine options ---------- */

function updateModeOptions() {
  const isDocument = elements.recognitionMode.value === "document";
  elements.docEngineField.hidden = !isDocument;
  // Nougat is selectable only once it is fully downloaded and ready.
  const nougatOption = elements.docEngine.querySelector('option[value="nougat"]');
  if (nougatOption) {
    nougatOption.disabled = !state.nougatReady;
    nougatOption.textContent = state.nougatReady ? t("docNougat") : t("docNougatUnavailable");
    if (!state.nougatReady && elements.docEngine.value === "nougat") {
      elements.docEngine.value = "layout";
    }
  }
}

/* ---------- file selection ---------- */

function addFiles(fileList) {
  const incoming = Array.from(fileList);
  const accepted = [];
  for (const file of incoming) {
    const extension = (file.name.split(".").pop() || "").toLowerCase();
    const allowed = ["pdf", "png", "jpg", "jpeg", "webp", "tif", "tiff"].includes(extension);
    if (!allowed) {
      showToast(t("unsupportedFile", { name: file.name }));
    } else if (file.size > MAX_FILE_BYTES) {
      showToast(t("fileTooLarge", { name: file.name }));
    } else {
      accepted.push(file);
    }
  }
  if (state.files.length + accepted.length > MAX_FILES) showToast(t("maximumFiles", { count: MAX_FILES }));
  state.files = [...state.files, ...accepted].slice(0, MAX_FILES);
  renderFiles();
  updateControls();
}

function renderFiles() {
  elements.fileList.replaceChildren();
  state.files.forEach((file, index) => {
    const row = document.createElement("div");
    row.className = "file-item";
    row.innerHTML = '<span class="file-type"></span><span class="file-name"></span><span class="file-size"></span><button type="button">×</button>';
    row.querySelector(".file-type").textContent = (file.name.split(".").pop() || "?").toUpperCase();
    row.querySelector(".file-name").textContent = file.name;
    row.querySelector(".file-size").textContent = humanBytes(file.size);
    const removeButton = row.querySelector("button");
    removeButton.setAttribute("aria-label", t("removeFile"));
    removeButton.addEventListener("click", () => {
      state.files.splice(index, 1);
      renderFiles();
      updateControls();
    });
    elements.fileList.append(row);
  });
}

/* ---------- recognition ---------- */

async function recognize() {
  if (!state.files.length || !state.online || state.busy) return;
  state.busy = true;
  updateControls();
  elements.progressPanel.hidden = false;
  elements.progressPanel.scrollIntoView({ behavior: "smooth", block: "center" });

  const body = new FormData();
  state.files.forEach((file) => body.append("files", file, file.name));
  body.append("mode", elements.recognitionMode.value);
  body.append("engine", elements.mathEngine.value);
  body.append("doc_engine", elements.docEngine.value);
  body.append("max_pdf_pages", elements.pageLimit.value);

  try {
    const response = await fetch(`${normalizedApiUrl()}/api/ocr`, { method: "POST", body });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || t("recognitionHttpFailed", { status: response.status }));
    state.results = payload.results || [];
    state.documents = payload.documents || [];
    renderDocuments();
    renderResults();
    (payload.warnings || []).forEach((warning) => showToast(warning));
    if (!payload.warnings || !payload.warnings.length) {
      showToast(state.results.length === 1 ? t("foundOne") : t("foundMany", { count: state.results.length }));
    }
    refreshStorage(); // sizes change after a first-run model download
  } catch (error) {
    showToast(error.message || t("recognitionFailed"));
  } finally {
    state.busy = false;
    elements.progressPanel.hidden = true;
    updateControls();
  }
}

function renderMath(latex, target) {
  target.textContent = latex;
  if (window.katex) {
    try {
      window.katex.render(latex, target, { displayMode: true, throwOnError: false, strict: "ignore" });
    } catch (_error) {
      target.textContent = latex;
    }
  }
}

function confidenceChip(confidence) {
  if (confidence == null) return null;
  const chip = document.createElement("span");
  const percent = Math.round(confidence * 100);
  chip.className = `confidence-chip ${percent >= 75 ? "high" : percent >= 45 ? "medium" : "low"}`;
  chip.textContent = `${percent}% ${t("confidence")}`;
  return chip;
}

function renderResults(shouldScroll = true) {
  elements.resultList.replaceChildren();
  elements.resultsSection.hidden = false;
  elements.resultsSummary.textContent = state.results.length
    ? `${state.results.length === 1 ? t("resultsOne") : t("resultsMany", { count: state.results.length })} ${t("reviewReminder")}`
    : t("noEquationsDetected");

  state.results.forEach((result, index) => {
    const card = document.createElement("article");
    card.className = "result-card";
    card.innerHTML = `
      <div class="result-source">
        <span class="result-origin"></span>
        <span class="result-badges"></span>
      </div>
      <div class="result-preview"></div>
      <div class="result-editor">
        <textarea spellcheck="false"></textarea>
        <div class="result-alternatives" hidden><span></span></div>
        <div class="result-actions">
          <button class="mini-button copy" type="button"></button>
          <button class="mini-button danger" type="button"></button>
        </div>
      </div>`;

    card.querySelector(".result-origin").textContent =
      result.page ? `${result.source} · ${t("page")} ${result.page}` : result.source;

    const badges = card.querySelector(".result-badges");
    const engineBadge = document.createElement("span");
    engineBadge.className = "engine-badge";
    engineBadge.textContent = ENGINE_SHORT_NAMES[result.engine] || result.engine;
    badges.append(engineBadge);
    const chip = confidenceChip(result.confidence);
    if (chip) badges.append(chip);

    const preview = card.querySelector(".result-preview");
    const textarea = card.querySelector("textarea");
    preview.setAttribute("aria-label", t("renderedPreview"));
    textarea.setAttribute("aria-label", t("editableLatex"));
    textarea.value = result.latex;
    renderMath(result.latex, preview);

    const alternativesRow = card.querySelector(".result-alternatives");
    if (result.alternatives && result.alternatives.length) {
      alternativesRow.hidden = false;
      alternativesRow.querySelector("span").textContent = t("alternativeReadings");
      for (const alternative of result.alternatives) {
        const chipButton = document.createElement("button");
        chipButton.type = "button";
        chipButton.className = "alternative-chip";
        chipButton.textContent = ENGINE_SHORT_NAMES[alternative.engine] || alternative.engine;
        chipButton.title = alternative.latex;
        chipButton.addEventListener("click", () => {
          // Swap: the current reading becomes the alternative.
          const previous = { engine: result.engine, latex: textarea.value.trim() };
          result.latex = alternative.latex;
          result.engine = alternative.engine;
          const position = result.alternatives.indexOf(alternative);
          result.alternatives.splice(position, 1, previous);
          renderResults(false);
        });
        alternativesRow.append(chipButton);
      }
    }

    textarea.addEventListener("input", () => {
      state.results[index].latex = textarea.value.trim();
      renderMath(textarea.value, preview);
    });
    const copyButton = card.querySelector(".copy");
    copyButton.textContent = t("copyLatex");
    copyButton.addEventListener("click", () => copyText(textarea.value, t("latexCopied")));
    const removeButton = card.querySelector(".danger");
    removeButton.textContent = t("remove");
    removeButton.addEventListener("click", () => {
      state.results.splice(index, 1);
      renderResults(false);
    });
    elements.resultList.append(card);
  });
  if (shouldScroll) elements.resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- document reconstruction view ---------- */

// Render a small subset of Markdown (paragraphs + $inline$ / $$display$$ math)
// into an element. No external Markdown library is needed for this preview.
function renderMarkdownPreview(markdown, target) {
  target.replaceChildren();
  const blocks = markdown.split(/\n{2,}/);
  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;
    const displayMatch = trimmed.match(/^\$\$([\s\S]+?)\$\$$/);
    if (displayMatch && window.katex) {
      const wrapper = document.createElement("div");
      wrapper.className = "doc-math";
      try {
        window.katex.render(displayMatch[1].trim(), wrapper, { displayMode: true, throwOnError: false, strict: "ignore" });
      } catch (_error) {
        wrapper.textContent = trimmed;
      }
      target.append(wrapper);
      continue;
    }
    const paragraph = document.createElement("p");
    const parts = trimmed.split(/(\$[^$]+\$)/);
    for (const part of parts) {
      const inline = part.match(/^\$([^$]+)\$$/);
      if (inline && window.katex) {
        const span = document.createElement("span");
        try {
          window.katex.render(inline[1], span, { displayMode: false, throwOnError: false, strict: "ignore" });
        } catch (_error) {
          span.textContent = part;
        }
        paragraph.append(span);
      } else if (part) {
        paragraph.append(document.createTextNode(part));
      }
    }
    target.append(paragraph);
  }
}

function renderDocuments() {
  const list = elements.documentList;
  list.replaceChildren();
  elements.documentSection.hidden = !state.documents.length;
  if (!state.documents.length) return;

  state.documents.forEach((doc, index) => {
    const card = document.createElement("article");
    card.className = "document-card";
    card.innerHTML = `
      <div class="document-source"></div>
      <div class="document-grid">
        <textarea class="document-editor" spellcheck="false"></textarea>
        <div class="document-preview"></div>
      </div>`;
    card.querySelector(".document-source").textContent =
      doc.page ? `${doc.source} · ${t("page")} ${doc.page}` : doc.source;
    const editor = card.querySelector(".document-editor");
    const preview = card.querySelector(".document-preview");
    editor.setAttribute("aria-label", t("editableDocument"));
    editor.value = doc.markdown;
    renderMarkdownPreview(doc.markdown, preview);
    editor.addEventListener("input", () => {
      state.documents[index].markdown = editor.value;
      renderMarkdownPreview(editor.value, preview);
    });
    list.append(card);
  });
}

function documentMarkdown() {
  return state.documents.map((doc) => doc.markdown.trim()).filter(Boolean).join("\n\n");
}

async function downloadDocumentWord() {
  const markdown = documentMarkdown();
  if (!markdown) return showToast(t("nothingToExport"));
  const button = elements.downloadDocWordButton;
  const label = button.textContent;
  button.disabled = true;
  button.textContent = t("buildingWord");
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/export/docx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: t("documentTitle"), markdown }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || t("wordFailed"));
    }
    downloadBlob(await response.blob(), exportFilename("docx"));
    showToast(t("wordCreated"));
  } catch (error) {
    showToast(error.message || t("wordFailed"));
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

/* ---------- export ---------- */

async function copyText(value, successMessage) {
  try {
    await navigator.clipboard.writeText(value);
    showToast(successMessage);
  } catch (_error) {
    showToast(t("clipboardBlocked"));
  }
}

function activeLatex() {
  return state.results.map((result) => result.latex.trim()).filter(Boolean);
}

function exportFilename(extension) {
  return `${t("texTitle")} ${AUTHOR_SUFFIX}.${extension}`;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}

function downloadTex() {
  const equations = activeLatex();
  if (!equations.length) return showToast(t("nothingToExport"));
  const body = equations.map((latex) => `\\[\n${latex}\n\\]`).join("\n\n");
  const tex = `% MathOCR export by Bouronikos Christos <chrisbouronikos@gmail.com>.\n% Support: https://paypal.me/christosbouronikos\n\\documentclass{article}\n\\usepackage{amsmath,amssymb}\n\\begin{document}\n${body}\n\\end{document}\n`;
  downloadBlob(new Blob([tex], { type: "application/x-tex;charset=utf-8" }), exportFilename("tex"));
}

async function downloadWord() {
  const equations = activeLatex();
  if (!equations.length) return showToast(t("nothingToExport"));
  const buttonText = elements.downloadWordButton.textContent;
  elements.downloadWordButton.disabled = true;
  elements.downloadWordButton.textContent = t("buildingWord");
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/export/docx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: t("texTitle"), equations }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || t("wordFailed"));
    }
    downloadBlob(await response.blob(), exportFilename("docx"));
    showToast(t("wordCreated"));
  } catch (error) {
    showToast(error.message || t("wordFailed"));
  } finally {
    elements.downloadWordButton.disabled = false;
    elements.downloadWordButton.textContent = buttonText;
  }
}

/* ---------- model storage ---------- */

async function refreshStorage() {
  if (!state.online) return renderStorage();
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/models`, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.storage = await response.json();
  } catch (_error) {
    state.storage = null;
  }
  renderStorage();
}

function renderStorage() {
  const list = elements.storageList;
  list.replaceChildren();
  if (!state.storage) {
    elements.storageTotalBytes.textContent = "—";
    elements.storagePathValue.textContent = "—";
    const note = document.createElement("p");
    note.className = "storage-note";
    note.textContent = t("storageUnavailable");
    list.append(note);
    elements.downloadModelsButton.disabled = true;
    elements.deleteAllModelsButton.disabled = true;
    return;
  }

  elements.storageTotalBytes.textContent = humanBytes(state.storage.total_bytes);
  elements.storagePathValue.textContent = state.storage.cache_root;
  elements.downloadModelsButton.disabled = state.busy;
  elements.deleteAllModelsButton.disabled = state.busy || !state.storage.total_bytes;

  for (const engine of state.storage.engines) {
    const row = document.createElement("div");
    row.className = "storage-row";
    row.innerHTML = `
      <div class="storage-name"><strong></strong><span class="storage-role"></span><span class="storage-status"></span></div>
      <span class="storage-size"></span>
      <span class="storage-action"></span>`;
    row.querySelector("strong").textContent = engine.label;
    const roleTag = row.querySelector(".storage-role");
    roleTag.textContent = t(`role_${engine.role}`);
    roleTag.classList.add(`role-${engine.role}`);
    const status = row.querySelector(".storage-status");
    const action = row.querySelector(".storage-action");

    // Nougat needs its optional package installed first; every other engine
    // is bundled with the app and can be fetched directly.
    if (engine.id === "nougat" && !engine.ready) {
      status.textContent = engine.installed ? t("storageWeightsMissing") : t("storageOptional");
      row.querySelector(".storage-size").textContent = "—";
      const installButton = document.createElement("button");
      installButton.type = "button";
      installButton.className = "mini-button install";
      installButton.textContent = t("downloadModel");
      installButton.disabled = !state.nougatInstallable && !engine.installed;
      if (installButton.disabled) installButton.title = t("nougatNeedsSource");
      installButton.addEventListener("click", installNougat);
      action.append(installButton);
      list.append(row);
      continue;
    }

    if (engine.loaded) status.textContent = t("storageLoaded");
    else if (engine.ready && !engine.bytes) status.textContent = t("storageReady");
    else if (!engine.installed) status.textContent = t("storageNotInstalled");
    else if (!engine.bytes) status.textContent = t("storageEmpty");
    row.querySelector(".storage-size").textContent = engine.bytes ? humanBytes(engine.bytes) : "—";

    const downloadButton = document.createElement("button");
    downloadButton.type = "button";
    downloadButton.className = "mini-button install";
    downloadButton.textContent = t("downloadModel");
    downloadButton.disabled = state.busy || !engine.ready;
    if (!engine.ready) downloadButton.title = t("storageNotInstalled");
    downloadButton.addEventListener("click", () => downloadEngine(engine.id, downloadButton));
    action.append(downloadButton);

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "mini-button danger";
    deleteButton.textContent = t("deleteModel");
    deleteButton.disabled = !engine.bytes;
    armConfirm(deleteButton, () => deleteModels(engine.id === "pix2text-mfr" ? "pix2text" : engine.id));
    action.append(deleteButton);
    list.append(row);
  }
}

async function installNougat() {
  showToast(t("installingNougat"));
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/models/nougat/install`, { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || t("nougatInstallFailed"));
    await checkService(); // refresh readiness so the dropdown enables Nougat
    showToast(state.nougatReady ? t("nougatReady") : t("nougatInstallFailed"));
  } catch (error) {
    showToast(error.message || t("nougatInstallFailed"));
  }
}

/**
 * Two-step inline confirmation: first click arms the button, second click
 * within four seconds executes. Native confirm() dialogs are unreliable
 * inside the desktop webview.
 */
function armConfirm(button, action) {
  let armed = false;
  let timer;
  const original = () => (button.dataset.originalText = button.dataset.originalText || button.textContent);
  button.addEventListener("click", () => {
    if (!armed) {
      original();
      armed = true;
      button.classList.add("armed");
      button.textContent = t("confirmDelete");
      timer = setTimeout(() => {
        armed = false;
        button.classList.remove("armed");
        button.textContent = button.dataset.originalText;
      }, 4000);
    } else {
      clearTimeout(timer);
      armed = false;
      button.classList.remove("armed");
      button.textContent = button.dataset.originalText;
      action();
    }
  });
}

async function deleteModels(engineId) {
  const query = engineId ? `?engine=${encodeURIComponent(engineId)}` : "";
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/models${query}`, { method: "DELETE" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const report = await response.json();
    if (report.failed_paths && report.failed_paths.length) {
      showToast(t("modelsDeleteFailed"));
    } else {
      showToast(t("modelsDeleted", { size: humanBytes(report.freed_bytes) }));
    }
  } catch (_error) {
    showToast(t("modelsDeleteFailed"));
  }
  refreshStorage();
}

async function downloadModels() {
  elements.downloadModelsButton.disabled = true;
  const original = elements.downloadModelsButton.textContent;
  elements.downloadModelsButton.textContent = t("downloadingModels");
  try {
    const response = await fetch(`${normalizedApiUrl()}/api/models/download`, { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await refreshStorage();
    showToast(t("modelsReady", { size: humanBytes(state.storage ? state.storage.total_bytes : 0) }));
  } catch (_error) {
    showToast(t("modelsDownloadFailed"));
  } finally {
    elements.downloadModelsButton.textContent = original;
    elements.downloadModelsButton.disabled = false;
    renderStorage();
  }
}

async function downloadEngine(engineId, button) {
  button.disabled = true;
  const original = button.textContent;
  button.textContent = t("downloadingModels");
  try {
    const response = await fetch(
      `${normalizedApiUrl()}/api/models/download?engine=${encodeURIComponent(engineId)}`,
      { method: "POST" }
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    await refreshStorage();
    showToast(t("modelsReady", { size: humanBytes(state.storage ? state.storage.total_bytes : 0) }));
  } catch (error) {
    showToast(error.message || t("modelsDownloadFailed"));
  } finally {
    renderStorage(); // rebuilds the row, so no need to restore original/disabled here
  }
}

/* ---------- events ---------- */

elements.fileInput.addEventListener("change", (event) => {
  addFiles(event.target.files);
  event.target.value = "";
});
["dragenter", "dragover"].forEach((eventName) =>
  document.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.add("dragging");
  }),
);
["dragleave", "drop"].forEach((eventName) =>
  document.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "dragleave" && event.relatedTarget) return;
    elements.dropZone.classList.remove("dragging");
  }),
);
document.addEventListener("drop", (event) => {
  if (event.dataTransfer && event.dataTransfer.files.length) addFiles(event.dataTransfer.files);
});
document.addEventListener("paste", (event) => {
  const items = Array.from(event.clipboardData ? event.clipboardData.items : []);
  const images = items
    .filter((item) => item.kind === "file" && item.type.startsWith("image/"))
    .map((item) => item.getAsFile())
    .filter(Boolean)
    .map((file, index) => {
      const extension = (file.type.split("/")[1] || "png").replace("jpeg", "jpg");
      const stamp = new Date().toISOString().slice(0, 19).replaceAll(":", "-");
      return new File([file], `pasted-${stamp}-${index + 1}.${extension}`, { type: file.type });
    });
  if (images.length) {
    addFiles(images);
    showToast(t("pastedImage"));
  }
});

elements.recognizeButton.addEventListener("click", recognize);
elements.recognitionMode.addEventListener("change", updateModeOptions);
elements.copyDocButton.addEventListener("click", () => copyText(documentMarkdown(), t("documentCopied")));
elements.downloadDocWordButton.addEventListener("click", downloadDocumentWord);
elements.recheckButton.addEventListener("click", checkService);
elements.refreshPageButton.addEventListener("click", () => location.reload());
elements.updateButton.addEventListener("click", installUpdate);
elements.apiUrl.addEventListener("change", () => {
  localStorage.setItem("mathocr-api-url", normalizedApiUrl());
  checkService();
});
elements.copyAllButton.addEventListener("click", () => copyText(activeLatex().join("\n\n"), t("allLatexCopied")));
elements.downloadTexButton.addEventListener("click", downloadTex);
elements.downloadWordButton.addEventListener("click", downloadWord);
elements.downloadModelsButton.addEventListener("click", downloadModels);
armConfirm(elements.deleteAllModelsButton, () => deleteModels(null));
document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => applyLanguage(button.dataset.language));
});

/* ---------- startup ---------- */

// The desktop launcher supplies its private random port through the query
// string. Browser and GitHub Pages use the remembered address or the default.
const suppliedApiUrl = params.get("api");
elements.apiUrl.value = suppliedApiUrl || localStorage.getItem("mathocr-api-url") || elements.apiUrl.value;
if (isDesktop) {
  elements.advancedSettings.hidden = true; // the port is private and per-launch
  elements.engineBanner.hidden = true;
}
elements.footerVersion.textContent = APP_VERSION;
applyLanguage(state.language);
checkService();
setInterval(() => {
  if (!state.busy && !state.online) checkService();
}, 5000);
