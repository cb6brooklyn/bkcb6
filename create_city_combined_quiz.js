/**
 * CB6 City Government & Charter Combined Quiz  --  15 questions
 * Source: Both NYC Gov and City Charter tabs on govhub.html
 * Run createCityCombinedQuiz() in Google Apps Script
 */

var COMBINED_TITLE = 'CB6 City Government & Charter  --  Combined Quiz';
var COMBINED_URL = 'https://bkcb6.app/govhub.html';
var COMBINED_TOTAL = 15;

function getCombinedRank(score) {
  var pct = Math.round((score / COMBINED_TOTAL) * 100);
  if (pct >= 95)  return { role: 'Mayor', message: 'Perfect. You know the structure and the history. The city runs on people who understand both.' };
  if (pct >= 80)  return { role: 'Deputy Mayor', message: 'You have a strong command of both the org chart and the charter. One more read closes the gap.' };
  if (pct >= 65)  return { role: 'Commissioner', message: 'You understand the system. A few pieces worth going back to sharpen.' };
  if (pct >= 50)  return { role: 'Deputy Commissioner', message: 'Solid foundation. The combined picture is worth another pass.' };
  if (pct >= 30)  return { role: 'Community Liaison', message: 'You are engaged. Keep reading  --  both tabs have what you need.' };
  return          { role: 'Resident', message: 'Start with the City Charter tab. Then the org chart. Then come back.' };
}

function createCityCombinedQuiz() {
  var questions = [
    // From Charter tab
    {
      q: 'The City Charter is described as what?',
      choices: [
        'The annual budget approved by the City Council',
        "The city's governing document  --  its constitution",
        'A state law passed by the Albany legislature',
        'A list of zoning rules for each neighborhood'
      ],
      answer: "The city's governing document  --  its constitution",
      exp: 'The charter defines the structure of city government: the powers of the Mayor, City Council, Borough Presidents, and Community Boards, and the rules that govern how the city operates day to day.'
    },
    // From Org Chart tab
    {
      q: 'Which body passes local laws, adopts the city budget, and has final say on land use via ULURP?',
      choices: ['The Mayor\'s Office', 'The City Council', 'The Borough Presidents', 'The Community Boards'],
      answer: 'The City Council',
      exp: 'The City Council  --  51 members  --  passes local laws, adopts the budget, and has final say on land use via ULURP.'
    },
    // From Charter tab
    {
      q: 'How are amendments to the City Charter adopted?',
      choices: [
        'The Mayor signs an executive order',
        'A Charter Revision Commission proposes them; voters approve as ballot questions',
        'The City Council votes by a two-thirds majority',
        'The State Legislature passes enabling legislation'
      ],
      answer: 'A Charter Revision Commission proposes them; voters approve as ballot questions',
      exp: 'A Charter Revision Commission reviews the charter and proposes amendments, which then go to voters as ballot questions.'
    },
    // From Org Chart tab
    {
      q: 'Community boards are advisory on three things. Which three?',
      choices: [
        'Zoning, elections, and public safety',
        'Land use, budgets, and local services',
        'Contracts, permits, and inspections',
        'Housing, transportation, and parks'
      ],
      answer: 'Land use, budgets, and local services',
      exp: 'Community boards are advisory  --  not binding  --  on land use, budgets, and local services.'
    },
    // From Charter tab
    {
      q: 'By what margin did Brooklyn vote for consolidation into Greater New York in 1894?',
      choices: ['27 votes', '277 votes', '2,770 votes', 'Brooklyn voted against it'],
      answer: '277 votes',
      exp: 'Brooklyn voted 64,744 in favor and 64,467 opposed  --  a margin of 277 votes out of more than 129,000 cast.'
    },
    // From Org Chart tab
    {
      q: 'Which agency designates and regulates historic landmarks and districts, and how many historic districts does CB6 have?',
      choices: [
        'DCP  --  four historic districts',
        'HPD  --  three historic districts',
        'LPC  --  six historic districts',
        'DOB  --  five historic districts'
      ],
      answer: 'LPC  --  six historic districts',
      exp: 'The Landmarks Preservation Commission designates and regulates historic landmarks and districts. CB6 has six historic districts and reviews Certificate of Appropriateness applications.'
    },
    // From Charter tab
    {
      q: 'What was created by the 1975 Charter Revision Commission?',
      choices: [
        'The five-borough structure of New York City',
        'Community boards and ULURP',
        'The position of Public Advocate',
        'Community board term limits'
      ],
      answer: 'Community boards and ULURP',
      exp: 'The 1975 CRC created community boards and the Uniform Land Use Review Procedure  --  the public review process CB6 uses today.'
    },
    // From Org Chart tab
    {
      q: 'DEP manages the Gowanus Canal Superfund. Which deputy mayor oversees DEP?',
      choices: [
        'Deputy Mayor for Housing & Planning',
        'Deputy Mayor for Health & Human Services',
        'Deputy Mayor for Operations',
        'First Deputy Mayor'
      ],
      answer: 'Deputy Mayor for Operations',
      exp: 'The Deputy Mayor for Operations oversees the agencies that keep the city running day to day, including DEP, DOT, DSNY, DPR, and DOB.'
    },
    // From Charter tab
    {
      q: 'What was "member deference" and why did the 2025 charter amendments target it?',
      choices: [
        'A requirement that CB votes be unanimous before going to the City Council',
        'An informal practice letting a council member effectively kill any development in their district',
        'A rule requiring the Mayor to defer to the City Council on budget amendments',
        'A term for seniority-based committee assignments in the Council'
      ],
      answer: 'An informal practice letting a council member effectively kill any development in their district',
      exp: 'Member deference is the informal norm by which the full Council follows the local member\'s lead on land use. If a member says no, the project dies. The 2025 amendments created faster tracks for affordable housing that bypass this.'
    },
    // From Org Chart tab
    {
      q: 'The Public Advocate is first in line of mayoral succession. What is their primary role?',
      choices: [
        'Oversees the city budget',
        'Ombudsman for New Yorkers  --  investigates complaints against city agencies',
        'Appoints community board members',
        'Chairs the City Planning Commission'
      ],
      answer: 'Ombudsman for New Yorkers  --  investigates complaints against city agencies',
      exp: 'The Public Advocate is ombudsman for New Yorkers, investigates complaints against city agencies, and serves as first in line of mayoral succession.'
    },
    // From Charter tab
    {
      q: 'How many new land use pathways did the 2025 charter amendments create, and when does the last one take effect?',
      choices: [
        'Two, both immediate',
        'Three, all immediate',
        'Four  --  three immediate, one taking effect in 2027',
        'Five  --  one per borough'
      ],
      answer: 'Four  --  three immediate, one taking effect in 2027',
      exp: 'Three pathways took effect immediately (ELURP-CC, BSA fast-track, ELURP-CPC) plus an Affordable Housing Fast Track taking effect in 2027, targeting the 12 community districts with the lowest affordable housing production.'
    },
    // From Org Chart tab
    {
      q: 'How many community boards are there citywide?',
      choices: ['51', '55', '59', '62'],
      answer: '59',
      exp: 'There are 59 community boards citywide across all five boroughs.'
    },
    // From Charter tab
    {
      q: 'How did every election district in CB6 vote on the 2025 pro-housing charter measures?',
      choices: [
        'Every ED rejected them',
        'Every ED approved them',
        'Most approved; a few in Park Slope rejected',
        'Results were mixed across neighborhoods'
      ],
      answer: 'Every ED approved them',
      exp: 'Every single ED in CB6 approved the pro-housing measures. The charter page notes: "The entities that claimed to speak for entire neighborhoods in CB6 didn\'t even win their own blocks."'
    },
    // From Org Chart tab
    {
      q: 'CB6 includes which two NYCHA developments?',
      choices: [
        'Red Hook Houses and Gowanus Houses',
        'Gowanus Houses and Wyckoff Gardens',
        'Wyckoff Gardens and Warren Street Houses',
        'Atlantic Terminal Houses and Gowanus Houses'
      ],
      answer: 'Gowanus Houses and Wyckoff Gardens',
      exp: 'CB6 includes Gowanus Houses and Wyckoff Gardens. Approximately $200M in capital investment was secured for them through the 2021 Gowanus rezoning.'
    },
    // From Charter tab
    {
      q: 'The charter page draws a parallel between 1894 Brooklyn and 2025 NYC. What is the parallel?',
      choices: [
        'Both involved the Brooklyn Daily Eagle running opposition campaigns',
        'Both involved the State Legislature overriding local vetoes',
        'The anti-consolidation and anti-housing arguments share the same structure: that newcomers and outside decisions will degrade existing communities',
        'Both measures ultimately failed citywide despite passing in CB6'
      ],
      answer: 'The anti-consolidation and anti-housing arguments share the same structure: that newcomers and outside decisions will degrade existing communities',
      exp: 'The charter page states: "The anti-consolidation arguments of 1894 Brooklyn and the anti-housing arguments of 2025 city council districts share the same structure: that newcomers and outside decisions will degrade existing communities."'
    }
  ];

  var form = FormApp.create(COMBINED_TITLE)
    .setDescription('15 questions drawing from both the NYC Government Org Chart and the City Charter.\n\nSource: ' + COMBINED_URL)
    .setIsQuiz(true)
    .setCollectEmail(true)
    .setShuffleQuestions(false)
    .setShowLinkToRespondAgain(true)
    .setProgressBar(true)
    .setConfirmationMessage('Thanks. Check your email for your score and rank.');

  var ss = SpreadsheetApp.create(COMBINED_TITLE + ' Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  for (var i = 0; i < questions.length; i++) {
    var q = questions[i];
    var item = form.addMultipleChoiceItem();
    item.setTitle((i + 1) + '. ' + q.q)
      .setChoices(q.choices.map(function(c) { return item.createChoice(c, c === q.answer); }))
      .setRequired(true)
      .setPoints(1)
      .setFeedbackForCorrect(FormApp.createFeedback().setText('Correct. ' + q.exp).addLink(COMBINED_URL, 'Review the page').build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.exp).addLink(COMBINED_URL, 'Review the page').build());
  }

  form.addTextItem()
    .setTitle('Optional: enter your initials for the leaderboard')
    .setRequired(false);

  setupCombinedSheets_(ss);
  deleteExistingCombinedTrigger_('onCityCombinedSubmit');
  ScriptApp.newTrigger('onCityCombinedSubmit').forForm(form).onFormSubmit().create();

  Logger.log('Form URL: ' + form.getPublishedUrl());
  Logger.log('Sheet URL: ' + ss.getUrl());
}

function onCityCombinedSubmit(e) {
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

  var pct = Math.round((score / COMBINED_TOTAL) * 100);
  var rank = getCombinedRank(score);

  updateCombinedLeaderboard_(ss, initials, score, wrong, pct, rank.role, timestamp);

  var statsSheet = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  var cell = statsSheet.getRange(1,1);
  cell.setValue((Number(cell.getValue()) || 0) + 1);

  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: 'CB6 City Gov & Charter Quiz: ' + score + '/' + COMBINED_TOTAL + '  --  ' + rank.role,
      body: 'CB6 City Government & Charter Combined Quiz\n\n' +
        'Score: ' + score + '/' + COMBINED_TOTAL + ' (' + pct + '%)\n' +
        'Rank: ' + rank.role + '\n\n' +
        rank.message + '\n\n' +
        (initials ? 'Leaderboard: ' + initials : 'No initials entered.') + '\n\n' +
        'Source: ' + COMBINED_URL
    });
  }
}

function setupCombinedSheets_(ss) {
  var lb = ss.getSheetByName('Leaderboard') || ss.insertSheet('Leaderboard');
  lb.clear();
  lb.getRange(1,1,1,7).setValues([['Rank','Initials','Score','Wrong','Pct','Role','Timestamp']]);
  var stats = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  stats.clear();
  stats.getRange(1,1).setValue(0);
}

function updateCombinedLeaderboard_(ss, initials, score, wrong, pct, role, timestamp) {
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

function deleteExistingCombinedTrigger_(fn) {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === fn) ScriptApp.deleteTrigger(triggers[i]);
  }
}
