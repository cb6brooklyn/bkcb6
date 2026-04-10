/**
 * CB6 NY State Government Quiz
 * Run createStateGovQuiz() to build the form
 */

const STATE_QUIZ_TITLE = 'CB6 NY State Government Quiz';
const STATE_PAGE_URL = 'https://bkcb6.app/govhub.html';
const STATE_CORE_COUNT = 15;
const STATE_BONUS_POINTS = 1;
const STATE_LEADERBOARD_SHEET = 'Leaderboard';
const STATE_STATS_SHEET = 'Leaderboard_Stats';
const STATE_META_SHEET = 'Quiz_Meta';

function getStateRank(score, total) {
  const pct = Math.round((score / total) * 100);
  if (pct >= 95) return { role: 'Governor', message: 'Flawless. You understand how Albany works and what it means for New York City. Run for something.' };
  if (pct >= 85) return { role: 'Lt. Governor', message: 'You know the state system at a high level. One more push and you are running the executive chamber.' };
  if (pct >= 70) return { role: 'Commissioner', message: 'You understand what the agencies do and who controls them. Solid command of the structure.' };
  if (pct >= 50) return { role: 'Deputy Secretary', message: 'You have the framework. Keep reading — the details in Albany matter as much as the headlines.' };
  if (pct >= 30) return { role: 'Advocate', message: 'You are starting to understand how state government affects your block. Keep going.' };
  return { role: 'Constituent', message: 'Albany feels distant — but it controls your rent laws, your liquor licenses, and your transit. Worth knowing.' };
}

function createStateGovQuiz() {
  const questions = [
    {
      title: "New York State's rent stabilization laws are administered by which agency?",
      choices: [
        'NYC Department of Housing Preservation & Development',
        'Homes and Community Renewal (HCR/DHCR)',
        'The State Legislature directly',
        "The Attorney General's office"
      ],
      answer: 'Homes and Community Renewal (HCR/DHCR)',
      explanation: 'DHCR, part of HCR, administers rent stabilization and rent control statewide. This is a state function even though it primarily affects NYC tenants.',
      points: 1, isBonus: false
    },
    {
      title: "The State Liquor Authority issues liquor licenses. What is a community board's role?",
      choices: [
        'Final approval authority',
        'Advisory — submits recommendations the SLA may consider',
        'No role — CB is a city body, SLA is state',
        'Veto power under the 500 Foot Law'
      ],
      answer: 'Advisory — submits recommendations the SLA may consider',
      explanation: 'Community boards are advisory to the SLA. The 500 Foot Law requires the SLA to hold a hearing when a new license would be within 500 feet of two existing licenses, but the CB recommendation is not binding.',
      points: 1, isBonus: false
    },
    {
      title: 'Which state agency oversees the Gowanus Canal Superfund cleanup?',
      choices: [
        'Department of Transportation',
        'Department of Environmental Conservation (DEC)',
        'Empire State Development',
        'Office of General Services'
      ],
      answer: 'Department of Environmental Conservation (DEC)',
      explanation: 'DEC regulates air, water, and land quality and oversees Superfund cleanups. The Gowanus Canal is on the federal Superfund list, but DEC coordinates with the EPA on the remediation.',
      points: 1, isBonus: false
    },
    {
      title: 'The Governor proposes the state budget. Who must approve it?',
      choices: [
        'The Lt. Governor',
        'The State Senate alone',
        'Both the State Senate and State Assembly',
        'The State Comptroller'
      ],
      answer: 'Both the State Senate and State Assembly',
      explanation: 'Both chambers of the legislature must pass the budget. The Governor proposes; the legislature negotiates and approves. The deadline is April 1 but is frequently missed.',
      points: 1, isBonus: false
    },
    {
      title: 'What makes the State Education Department unusual compared to other state agencies?',
      choices: [
        'It is funded entirely by the federal government',
        'Its commissioner is appointed by the Board of Regents, not the Governor',
        'It operates independently of the state budget',
        'It is run by the City of New York'
      ],
      answer: 'Its commissioner is appointed by the Board of Regents, not the Governor',
      explanation: 'The Commissioner of Education is appointed by the Board of Regents, an elected body. This makes NYSED one of the few state agencies not directly controlled by the Governor.',
      points: 1, isBonus: false
    },
    {
      title: "Con Edison sets its electricity rates with approval from which state body?",
      choices: [
        'The State Legislature',
        "The Governor's office",
        'The Public Service Commission',
        'The Department of Financial Services'
      ],
      answer: 'The Public Service Commission',
      explanation: "The PSC regulates electric, gas, water, and telecom utilities. When Con Edison files for a rate increase, the PSC holds hearings and issues a final order. This directly affects CB6 residents and businesses.",
      points: 1, isBonus: false
    },
    {
      title: "NYSERDA's primary focus is:",
      choices: [
        "Regulating the state's banks",
        'Advancing clean energy and administering efficiency programs',
        'Managing state parks',
        'Overseeing public housing statewide'
      ],
      answer: 'Advancing clean energy and administering efficiency programs',
      explanation: 'NYSERDA funds clean energy research, administers efficiency rebate programs, and has been central to New York\'s offshore wind development — relevant to Red Hook and the Brooklyn waterfront.',
      points: 1, isBonus: false
    },
    {
      title: 'A developer wants state financing for an affordable housing project in CB6. Which agency is the primary source?',
      choices: [
        'Empire State Development',
        'NYS Department of Transportation',
        'Homes and Community Renewal (HCR)',
        'Office of the State Comptroller'
      ],
      answer: 'Homes and Community Renewal (HCR)',
      explanation: "HCR is New York State's affordable housing agency. It administers LIHTC, HOME funds, and state housing finance programs. Most affordable housing in CB6 that uses state financing goes through HCR.",
      points: 1, isBonus: false
    },
    {
      title: "The State Comptroller's most significant ongoing responsibility is:",
      choices: [
        'Appointing agency commissioners',
        'Managing the state pension fund and auditing agencies',
        'Presiding over the State Senate',
        'Setting tax rates'
      ],
      answer: 'Managing the state pension fund and auditing agencies',
      explanation: 'The Comptroller manages the New York State Common Retirement Fund — one of the largest pension funds in the country — and independently audits state agencies and local governments.',
      points: 1, isBonus: false
    },
    {
      title: "Which branch of the NY State Legislature confirms the Governor's appointments?",
      choices: [
        'The State Assembly',
        'Both chambers jointly',
        'The State Senate',
        'The Lt. Governor'
      ],
      answer: 'The State Senate',
      explanation: "The State Senate alone has the power to confirm the Governor's appointments of non-elected state officials and court judges. The Assembly does not participate in confirmation.",
      points: 1, isBonus: false
    },
    {
      title: 'Assembly District 52 covers parts of CB6. Who represents it?',
      choices: ['Robert Carroll', 'Jo Anne Simon', 'Jabari Brisport', 'Andrew Gounardes'],
      answer: 'Jo Anne Simon',
      explanation: 'Jo Anne Simon represents AD 52, which covers Carroll Gardens, Cobble Hill, and parts of Red Hook. Robert Carroll represents AD 44, which covers Park Slope and Gowanus.',
      points: 1, isBonus: false
    },
    {
      title: 'The 500 Foot Law affects liquor license applications. Which agency enforces it?',
      choices: [
        'NYC Department of Consumer & Worker Protection',
        'NYC Community Boards',
        'State Liquor Authority',
        'NY State Attorney General'
      ],
      answer: 'State Liquor Authority',
      explanation: 'The 500 Foot Law is a provision of the Alcoholic Beverage Control Law, enforced by the SLA. It requires a hearing when a new on-premises license would be within 500 feet of two or more existing licenses.',
      points: 1, isBonus: false
    },
    {
      title: "Empire State Development's role in Brooklyn is most directly connected to:",
      choices: [
        'Managing the subway',
        'The Brooklyn Marine Terminal redevelopment',
        'Administering rent stabilization',
        'Issuing building permits'
      ],
      answer: 'The Brooklyn Marine Terminal redevelopment',
      explanation: "ESD is the state's primary economic development agency. The Brooklyn Marine Terminal — a major project adjacent to CB6 — involves ESD coordinating the redevelopment of the waterfront site with NYCEDC and private developers.",
      points: 1, isBonus: false
    },
    {
      title: "The Attorney General's office has investigated predatory equity landlords in NYC. Under what authority?",
      choices: [
        'The AG enforces consumer protection and civil rights laws statewide',
        'The AG oversees all NYC agencies',
        'The AG must be invited in by the Mayor',
        'The AG only handles criminal cases'
      ],
      answer: 'The AG enforces consumer protection and civil rights laws statewide',
      explanation: 'The AG has broad authority to enforce state consumer protection and civil rights laws, investigate fraud, and pursue cases involving tenant harassment. The AG operates independently of the Mayor and city agencies.',
      points: 1, isBonus: false
    },
    {
      title: 'State Senate District 26 covers much of CB6. Who represents it?',
      choices: ['Julia Salazar', 'Jabari Brisport', 'Andrew Gounardes', 'Zellnor Myrie'],
      answer: 'Andrew Gounardes',
      explanation: 'Andrew Gounardes represents SD 26, covering much of CB6 including Park Slope, Carroll Gardens, Cobble Hill, and Red Hook. Julia Salazar (SD 18) and Jabari Brisport (SD 25) cover neighboring districts.',
      points: 1, isBonus: false
    },
    {
      title: 'Bonus: The MTA is a state authority. When NYC wants the subway fixed, who ultimately controls the capital budget?',
      choices: [
        'The NYC Mayor, who funds the MTA directly',
        'The Governor, who appoints the MTA board majority and controls capital plan approval',
        'The State Legislature, which votes on each capital project',
        'The MTA board, which operates fully independently'
      ],
      answer: 'The Governor, who appoints the MTA board majority and controls capital plan approval',
      explanation: "The Governor appoints a majority of the MTA board and the MTA chair. Capital plans require state approval. This is why MTA funding is an Albany fight, not just a city budget fight.",
      points: 1, isBonus: true
    }
  ];

  const form = FormApp.create(STATE_QUIZ_TITLE)
    .setDescription(
      'A 15-question quiz plus 1 bonus on NY State government — who runs what, what they control, and why it matters for Brooklyn.\n\n' +
      'Source: ' + STATE_PAGE_URL + '\n\n' +
      'Questions test understanding, not memorization.'
    )
    .setIsQuiz(true)
    .setCollectEmail(true)
    .setShuffleQuestions(false)
    .setAllowResponseEdits(false)
    .setPublishingSummary(false)
    .setShowLinkToRespondAgain(true)
    .setProgressBar(true)
    .setConfirmationMessage('Thanks for taking the quiz. Check your email for your score and rank.');

  const spreadsheet = SpreadsheetApp.create(STATE_QUIZ_TITLE + ' Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());

  questions.forEach((q, idx) => {
    const item = form.addMultipleChoiceItem();
    const prefix = q.isBonus ? 'Bonus. ' : (idx + 1) + '. ';
    item.setTitle(prefix + q.title)
      .setChoices(q.choices.map(c => item.createChoice(c, c === q.answer)))
      .setRequired(true)
      .setPoints(q.points)
      .setFeedbackForCorrect(
        FormApp.createFeedback().setText('Correct. ' + q.explanation).addLink(STATE_PAGE_URL, 'Review the page').build()
      )
      .setFeedbackForIncorrect(
        FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.explanation).addLink(STATE_PAGE_URL, 'Review the page').build()
      );
  });

  form.addTextItem()
    .setTitle('Optional: enter your initials for the leaderboard')
    .setRequired(false)
    .setHelpText('Leave blank if you do not want to appear on the leaderboard.');

  // Set up sheets
  const metaSheet = getOrCreateSheetState_(spreadsheet, STATE_META_SHEET);
  metaSheet.clear();
  metaSheet.getRange(1,1,1,6).setValues([['Q#','Title','Answer','Explanation','Points','Bonus']]);
  questions.forEach((q,i) => metaSheet.getRange(i+2,1,1,6).setValues([[i+1,q.title,q.answer,q.explanation,q.points,q.isBonus]]));
  metaSheet.hideSheet();

  const lb = getOrCreateSheetState_(spreadsheet, STATE_LEADERBOARD_SHEET);
  lb.clear();
  lb.getRange(1,1,1,9).setValues([['Rank','Initials','Score','Wrong','Pct','Bonus','Total','Role','Timestamp']]);

  const stats = getOrCreateSheetState_(spreadsheet, STATE_STATS_SHEET);
  stats.clear();
  stats.getRange(1,1,2,2).setValues([['Metric','Value'],['Total Takers',0]]);

  deleteExistingTriggerState_('onStateGovSubmit');
  ScriptApp.newTrigger('onStateGovSubmit').forForm(form).onFormSubmit().create();

  Logger.log('Form: ' + form.getPublishedUrl());
  Logger.log('Sheet: ' + spreadsheet.getUrl());
}

function onStateGovSubmit(e) {
  const response = e.response;
  const email = response.getRespondentEmail() || '';
  const timestamp = response.getTimestamp();
  const itemResponses = response.getItemResponses();
  const form = FormApp.getActiveForm();
  const ss = SpreadsheetApp.openById(form.getDestinationId());

  let initials = '', coreScore = 0, bonusScore = 0, wrong = 0, total = 0;

  itemResponses.forEach(ir => {
    const item = ir.getItem();
    const title = item.getTitle();
    if (title === 'Optional: enter your initials for the leaderboard') {
      initials = String(ir.getResponse() || '').trim().toUpperCase();
      return;
    }
    if (item.getType() !== FormApp.ItemType.MULTIPLE_CHOICE) return;
    const mc = item.asMultipleChoiceItem();
    const correct = (mc.getChoices().find(c => c.isCorrectAnswer()) || {getValue: function(){return '';}}).getValue();
    const isCorrect = String(ir.getResponse()) === correct;
    const isBonus = title.startsWith('Bonus.');
    if (isBonus) { if (isCorrect) { bonusScore++; total++; } }
    else { if (isCorrect) { coreScore++; total++; } else { wrong++; } }
  });

  const stats = getOrCreateSheetState_(ss, STATE_STATS_SHEET);
  const cell = stats.getRange(2,2);
  const newTotal = (Number(cell.getValue()) || 0) + 1;
  cell.setValue(newTotal);

  const pct = Math.round((coreScore / STATE_CORE_COUNT) * 100);
  const rank = getStateRank(coreScore, STATE_CORE_COUNT);

  if (initials) {
    const lb = getOrCreateSheetState_(ss, STATE_LEADERBOARD_SHEET);
    lb.appendRow(['', initials, coreScore, wrong, pct, bonusScore, total, rank.role, timestamp]);
    const last = lb.getLastRow();
    if (last > 2) lb.getRange(2,1,last-1,9).sort([{column:3,ascending:false},{column:9,ascending:true}]);
    if (lb.getLastRow() > 11) lb.deleteRows(12, lb.getLastRow()-11);
    const count = lb.getLastRow()-1;
    if (count > 0) lb.getRange(2,1,count,1).setValues(Array.from({length:count}, function(_,i){return [[i+1]];}));
  }

  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: 'Your CB6 State Gov Quiz result: ' + coreScore + '/' + STATE_CORE_COUNT + ' — ' + rank.role,
      body: 'Thanks for taking the CB6 NY State Government Quiz.\n\n' +
        'Score: ' + coreScore + ' correct, ' + wrong + ' wrong (' + pct + '%)\n' +
        'Bonus: ' + bonusScore + '/1\n' +
        'Total score: ' + total + '/' + (STATE_CORE_COUNT + STATE_BONUS_POINTS) + '\n\n' +
        'Your rank: ' + rank.role + '\n\n' +
        rank.message + '\n\n' +
        'Total quiz takers so far: ' + newTotal + '\n\n' +
        (initials ? 'Leaderboard initials: ' + initials : 'You did not enter initials for the leaderboard.') + '\n\n' +
        'Review the source page: ' + STATE_PAGE_URL
    });
  }
}

function getOrCreateSheetState_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}
function deleteExistingTriggerState_(fn) {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === fn) ScriptApp.deleteTrigger(t); });
}
