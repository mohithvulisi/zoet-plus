const toxicTerms = [
  "idiot",
  "stupid",
  "shut up",
  "useless",
  "trash",
  "bloody",
  "hate",
  "kill",
  "nonsense",
  "dumb",
  "fuck",
  "puka",
  "dengey",
  "chutiye",
  "gandu",
  "bhosdi",
  "madarchod",
  "behenchod",
  "randi",
  "suar",
  "harami",
  "loda",
  "lodu",
  "bhen ke lode",
  "erripuka",
];

export function moderateText(text) {
  const normalized = String(text || "").toLowerCase();
  const matchedTerms = toxicTerms.filter((term) => normalized.includes(term));
  const toxicityScore = Math.min(99, matchedTerms.length * 35 + (normalized.length > 120 ? 10 : 0));

  if (toxicityScore >= 70) {
    return {
      label: "toxic",
      toxicityScore,
      blocked: true,
      action: "block_message_and_recommend_mute",
      matchedTerms
    };
  }

  if (toxicityScore >= 40) {
    return {
      label: "possibly_toxic",
      toxicityScore,
      blocked: true,
      action: "hold_message_and_warn_user",
      matchedTerms
    };
  }

  return {
    label: "safe",
    toxicityScore,
    blocked: false,
    action: "allow",
    matchedTerms
  };
}
