/**
 * CB6 City Charter Quiz  --  10 questions
 * Source: City Charter tab on govhub.html
 * Run createCityCharterQuiz() in Google Apps Script
 */

var CHARTER_TITLE = 'CB6 City Charter Quiz';
var CHARTER_URL = 'https://bkcb6.app/govhub.html';
var CHARTER_TOTAL = 10;

function getCharterRank(score) {
  var pct = Math.round((score / CHARTER_TOTAL) * 100);
  if (pct === 100) return { role: 'Charter Commissioner', message: 'Perfect. You know the document that governs the city  --  and the history behind it.' };
  if (pct >= 80)   return { role: 'Civic Advocate', message: 'Strong grasp of charter history and structure. You understand why this stuff matters.' };
  if (pct >= 60)   return { role: 'Informed Citizen', message: 'You have the key pieces. A few gaps worth filling before the next ballot.' };
  if (pct >= 40)   return { role: 'Engaged Resident', message: 'Solid start. The charter page is worth another read.' };
  return           { role: 'Resident', message: 'The charter is long but the key points are short. Start with the 2025 changes.' };
}

function createCityCharterQuiz() {
  var questions = [
    {
      q: 'What is the NYC City Charter?',
      choices: [
        'A list of city agency phone numbers',
        "The city's governing document  --  defining the structure of government, powers of elected officials, and how decisions get made",
        'A state law passed by the Albany legislature',
        'The annual budget approved by the City Council'
      ],
      answer: "The city's governing document  --  defining the structure of government, powers of elected officials, and how decisions get made",
      exp: 'The charter is described as "the city\'s constitution." It defines the powers of the Mayor, City Council, Borough Presidents, and Community Boards, and how land use and budgets work.'
    },
    {
      q: 'How are changes to the City Charter proposed and approved?',
      choices: [
        'The Mayor proposes changes; the City Council approves',
        'A Charter Revision Commission proposes amendments, which go to voters as ballot questions',
        'The State Legislature amends it annually',
        'The five Borough Presidents vote on changes jointly'
      ],
      answer: 'A Charter Revision Commission proposes amendments, which go to voters as ballot questions',
      exp: 'A Charter Revision Commission can be convened to review the charter and propose amendments. Those amendments then go to voters as ballot questions.'
    },
    {
      q: 'By what margin did Brooklyn vote in favor of consolidation into Greater New York in 1894?',
      choices: ['27 votes', '277 votes', '2,770 votes', 'Brooklyn voted against it'],
      answer: '277 votes',
      exp: 'Brooklyn voted 64,744 in favor and 64,467 opposed  --  a margin of 277 votes out of more than 129,000 cast.'
    },
    {
      q: 'Who is most credited with pushing the consolidation of New York City forward?',
      choices: ['Thomas C. Platt', 'Andrew H. Green', 'Governor Morton', 'The Brooklyn Daily Eagle'],
      answer: 'Andrew H. Green',
      exp: 'Andrew H. Green is most credited with pushing consolidation forward, writing as far back as 1868 that the region needed to be brought under one common municipal government.'
    },
    {
      q: 'The charter page describes what year as when community boards and ULURP were created?',
      choices: ['1898', '1938', '1975', '1989'],
      answer: '1975',
      exp: 'A 1975 Charter Revision Commission created community boards and the Uniform Land Use Review Procedure  --  the public review process CB6 uses today.'
    },
    {
      q: 'What was the central issue targeted by the 2025 charter amendments?',
      choices: [
        'The number of community board members',
        'Member deference  --  the informal practice letting a council member effectively veto development in their district',
        'The length of the mayoral term',
        'The Borough President appointment process'
      ],
      answer: 'Member deference  --  the informal practice letting a council member effectively veto development in their district',
      exp: 'The central issue was member deference: by long-standing tradition, the full Council defers to the local member on land use. If a member says no, the project dies. The 2025 amendments created tracks that bypass this.'
    },
    {
      q: 'How many new ULURP pathways did the 2025 charter amendments create?',
      choices: ['One', 'Two', 'Three', 'Four  --  including one taking effect in 2027'],
      answer: 'Four  --  including one taking effect in 2027',
      exp: 'The 2025 amendments created three immediate pathways (ELURP-CC, BSA fast-track, ELURP-CPC) plus a fourth Affordable Housing Fast Track taking effect in 2027 targeting the 12 districts with the lowest affordable housing production.'
    },
    {
      q: 'How did every election district in CB6 vote on the 2025 pro-housing charter measures?',
      choices: [
        'Narrowly in favor',
        'Narrowly against',
        'Every single ED approved them',
        'Split  --  some EDs approved, some rejected'
      ],
      answer: 'Every single ED approved them',
      exp: 'The charter page notes: "Every single ED in CB6 approved the pro-housing measures." Questions 2, 3, and 4  --  the housing measures  --  passed with over 56% of the vote citywide.'
    },
    {
      q: 'What does the charter page say about Yonkers and why it did not get annexed into New York City?',
      choices: [
        'Yonkers voters rejected annexation in a referendum',
        'Yonkers had invested in its own infrastructure and could supply its own services, reducing its need to join',
        'The State Legislature excluded Yonkers from the consolidation bill',
        'Yonkers was in a different county and legally ineligible'
      ],
      answer: 'Yonkers had invested in its own infrastructure and could supply its own services, reducing its need to join',
      exp: 'As the charter page explains: communities that could supply their own services had less reason to join New York, while those that could not had more. Yonkers had already invested heavily in streets, sewers, and a water supply.'
    },
    {
      q: 'The charter page draws a parallel between two sets of arguments made roughly 130 years apart. What is that parallel?',
      choices: [
        'Both involved Brooklyn newspapers running opposition campaigns',
        'Both involved the State Legislature overriding local vetoes',
        'The anti-consolidation arguments of 1894 and the anti-housing arguments of 2025 share the same structure: that newcomers and outside decisions will degrade existing communities',
        'Both resulted in measures failing citywide but passing in CB6'
      ],
      answer: 'The anti-consolidation arguments of 1894 and the anti-housing arguments of 2025 share the same structure: that newcomers and outside decisions will degrade existing communities',
      exp: 'The charter page states directly: "The anti-consolidation arguments of 1894 Brooklyn and the anti-housing arguments of 2025 city council districts share the same structure: that newcomers and outside decisions will degrade existing communities."'
    }
  ];

  var form = FormApp.create(CHARTER_TITLE)
    .setDescription('10 questions on the NYC City Charter  --  what it is, how it has changed, and why it matters.\n\nSource: ' + CHARTER_URL)
    .setIsQuiz(true)
    .setCollectEmail(true)
    .setShuffleQuestions(false)
    .setShowLinkToRespondAgain(true)
    .setProgressBar(true)
    .setConfirmationMessage('Thanks. Check your email for your score and rank.');

  var ss = SpreadsheetApp.create(CHARTER_TITLE + ' Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  for (var i = 0; i < questions.length; i++) {
    var q = questions[i];
    var item = form.addMultipleChoiceItem();
    item.setTitle((i + 1) + '. ' + q.q)
      .setChoices(q.choices.map(function(c) { return item.createChoice(c, c === q.answer); }))
      .setRequired(true)
      .setPoints(1)
      .setFeedbackForCorrect(FormApp.createFeedback().setText('Correct. ' + q.exp).addLink(CHARTER_URL, 'Review the page').build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.exp).addLink(CHARTER_URL, 'Review the page').build());
  }

  form.addTextItem()
    .setTitle('Optional: enter your initials for the leaderboard')
    .setRequired(false);

  setupCharterSheets_(ss);
  deleteExistingCharterTrigger_('onCityCharterSubmit');
  ScriptApp.newTrigger('onCityCharterSubmit').forForm(form).onFormSubmit().create();

  Logger.log('Form URL: ' + form.getPublishedUrl());
  Logger.log('Sheet URL: ' + ss.getUrl());
}

function onCityCharterSubmit(e) {
  var response = e.response;
  var email = response.getRespondentEmail() || '';
  var timestamp = response.getTimestamp();
  var items = response.getItemResponses();
  var form = FormApp.getActiveForm();
  var ss = SpreadsheetApp.openById(form.getDestinationId());

  var score = 0, wrong = 0, initials = '';
  for (var i = 0; i < items.length; i++) {
    var ir = items[i];
    var item = ir.getItem();
    var title = item.getTitle();
    if (title === 'Optional: enter your initials for the leaderboard') {
      initials = String(ir.getResponse() || '').trim().toUpperCase();
      continue;
    }
    if (item.getType() !== FormApp.ItemType.MULTIPLE_CHOICE) continue;
    var mc = item.asMultipleChoiceItem();
    var choices = mc.getChoices();
    var correct = '';
    for (var j = 0; j < choices.length; j++) { if (choices[j].isCorrectAnswer()) { correct = choices[j].getValue(); break; } }
    if (String(ir.getResponse()) === correct) { score++; } else { wrong++; }
  }

  var pct = Math.round((score / CHARTER_TOTAL) * 100);
  var rank = getCharterRank(score);

  updateCharterLeaderboard_(ss, initials, score, wrong, pct, rank.role, timestamp);

  var statsSheet = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  var cell = statsSheet.getRange(1,1);
  cell.setValue((Number(cell.getValue()) || 0) + 1);

  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: 'CB6 Charter Quiz: ' + score + '/' + CHARTER_TOTAL + '  --  ' + rank.role,
      body: 'CB6 City Charter Quiz\n\n' +
        'Score: ' + score + '/' + CHARTER_TOTAL + ' (' + pct + '%)\n' +
        'Rank: ' + rank.role + '\n\n' +
        rank.message + '\n\n' +
        (initials ? 'Leaderboard: ' + initials : 'No initials entered.') + '\n\n' +
        'Source: ' + CHARTER_URL
    });
  }
}

function setupCharterSheets_(ss) {
  var lb = ss.getSheetByName('Leaderboard') || ss.insertSheet('Leaderboard');
  lb.clear();
  lb.getRange(1,1,1,7).setValues([['Rank','Initials','Score','Wrong','Pct','Role','Timestamp']]);
  var stats = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  stats.clear();
  stats.getRange(1,1).setValue(0);
}

function updateCharterLeaderboard_(ss, initials, score, wrong, pct, role, timestamp) {
  if (!initials) return;
  var lb = ss.getSheetByName('Leaderboard') || ss.insertSheet('Leaderboard');
  lb.appendRow(['', initials, score, wrong, pct, role, timestamp]);
  var last = lb.getLastRow();
  if (last > 2) lb.getRange(2,1,last-1,7).sort([{column:3,ascending:false},{column:7,ascending:true}]);
  if (lb.getLastRow() > 11) lb.deleteRows(12, lb.getLastRow()-11);
  var count = lb.getLastRow()-1;
  if (count > 0) {
    var ranks = [];
    for (var i = 0; i < count; i++) { ranks.push([i+1]); }
    lb.getRange(2,1,count,1).setValues(ranks);
  }
}

function deleteExistingCharterTrigger_(fn) {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === fn) ScriptApp.deleteTrigger(triggers[i]);
  }
}
