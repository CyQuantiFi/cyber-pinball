// Sample data for previewing the page: open index.html?data=sample_data.js
// Same shape as the ThreatTide_leaderboard.js the table writes. "day" is
// filled with today's date so the sample always shows.
(function () {
  var d = new Date();
  var day = d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0");
  window.TT_LEADERBOARD = {
    board: {
      day: day,
      updated: d.toISOString(),
      scores: [
        { rank: 1, initials: "SKO", score: 48210000, score_text: "$48,210,000" },
        { rank: 2, initials: "JMW", score: 21875500, score_text: "$21,875,500" },
        { rank: 3, initials: "ACE", score: 12404000, score_text: "$12,404,000" },
        { rank: 4, initials: "RIS", score: 8312500, score_text: "$8,312,500" },
        { rank: 5, initials: "CSO", score: 6050000, score_text: "$6,050,000" },
        { rank: 6, initials: "BOB", score: 3975250, score_text: "$3,975,250" },
        { rank: 7, initials: "IRL", score: 2210000, score_text: "$2,210,000" },
        { rank: 8, initials: "AAA", score: 1230000, score_text: "$1,230,000" }
      ]
    },
    last_game: {
      ts: d.toISOString(), day: day, initials: "ACE", score: 12404000, score_text: "$12,404,000", rank: 3,
      worst_path: 4930000,
      worst_path_techniques: [
        { stage: "Recon", id: "T1595", technique: "Active Scanning" },
        { stage: "Initial Access", id: "T1566", technique: "Phishing" },
        { stage: "Execution", id: "T1059", technique: "Command and Scripting Interpreter" },
        { stage: "Persistence", id: "T1136", technique: "Create Account" },
        { stage: "Privilege Escalation", id: "T1078", technique: "Valid Accounts" },
        { stage: "Lateral Movement", id: "T1021", technique: "Remote Services" },
        { stage: "Impact", id: "T1486", technique: "Data Encrypted for Impact" }
      ],
      paths: 3, assets: 7, multiballs: 1, agreements: 2, storm_surge: true, tail_jackpot: 3150000, air_gap: true
    }
  };
})();
