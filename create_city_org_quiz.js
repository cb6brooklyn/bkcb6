/**
 * CB6 NYC Government Org Chart Quiz -- 10 questions
 * Run createCityOrgQuiz() in Google Apps Script
 */

var CITY_ORG_TITLE = 'CB6 NYC Government Org Chart Quiz';
var CITY_ORG_URL = 'https://bkcb6.app/govhub.html';
var CITY_ORG_TOTAL = 10;

function getCityOrgRank(score) {
  var pct = Math.round((score / CITY_ORG_TOTAL) * 100);
  if (pct === 100) return { role: 'Mayor', message: 'Perfect. You know the structure cold.' };
  if (pct >= 80)   return { role: 'Deputy Mayor', message: 'Strong command of how the city is organized.' };
  if (pct >= 60)   return { role: 'Commissioner', message: 'You have the key pieces. A few gaps worth filling.' };
  if (pct >= 40)   return { role: 'Deputy Commissioner', message: 'Solid start. Worth another read.' };
  return           { role: 'Community Liaison', message: 'You are in the room. Keep reading.' };
}

function createCityOrgQuiz() {
  var questions = [
    {
      q: 'Which citywide elected official functions as an independent financial watchdog, responsible for auditing city agencies and managing pension funds?',
      choices: ['Public Advocate', 'Comptroller', 'Mayor', 'Borough President'],
      answer: 'Comptroller',
      exp: 'The Comptroller is independently elected and serves as the city\'s financial watchdog -- auditing agencies, managing pension funds, and reviewing contracts.'
    },
    {
      q: 'The Department of City Planning (DCP) and the Landmarks Preservation Commission (LPC) are part of the portfolio of which Deputy Mayor?',
      choices: ['Deputy Mayor for Housing & Planning', 'Deputy Mayor for Economic Justice', 'Deputy Mayor for Operations', 'First Deputy Mayor'],
      answer: 'Deputy Mayor for Housing & Planning',
      exp: 'DCP and LPC both fall under the Deputy Mayor for Housing & Planning (Leila Bozorg), along with NYCHA, HPD, DOB, PDC, and the Office to Protect Tenants.'
    },
    {
      q: 'Who serves as first in line of mayoral succession in NYC?',
      choices: ['Comptroller', 'Public Advocate', 'Speaker of the City Council', 'First Deputy Mayor'],
      answer: 'Public Advocate',
      exp: 'The Public Advocate is ombudsman for New Yorkers -- investigating complaints against city agencies -- and is first in line of mayoral succession.'
    },
    {
      q: 'Which of the following is NOT a responsibility of Borough Presidents?',
      choices: ['Appointing Community Board members', 'Advocating for borough needs', 'Independently directing District Attorneys', 'Serving an advisory role in land use'],
      answer: 'Independently directing District Attorneys',
      exp: 'District Attorneys are independently elected and not directed by anyone -- not the Mayor, not Borough Presidents. Borough Presidents appoint CB members, advocate for borough needs, and play an advisory role in land use.'
    },
    {
      q: 'The Office of Gun Violence Prevention and the Office for Prevention of Hate Crimes fall under which Deputy Mayor?',
      choices: ['First Deputy Mayor', 'Deputy Mayor for Health & Human Services', 'Deputy Mayor for Community Safety', 'Deputy Mayor for Economic Justice'],
      answer: 'Deputy Mayor for Community Safety',
      exp: 'The Deputy Mayor for Community Safety (Renita Francois) oversees the Office of Community Safety, which includes the Office of Gun Violence Prevention and the Office for Prevention of Hate Crimes.'
    },
    {
      q: 'How many members comprise the NYC City Council?',
      choices: ['5', '51', '59', '100'],
      answer: '51',
      exp: 'The NYC City Council has 51 members. It passes local laws, adopts the budget, and has a role in land use review.'
    },
    {
      q: 'Which Deputy Mayor is responsible for overseeing the NYPD and the Department of Correction?',
      choices: ['Deputy Mayor for Operations', 'Deputy Mayor for Community Safety', 'First Deputy Mayor', 'Deputy Mayor for Health & Human Services'],
      answer: 'First Deputy Mayor',
      exp: 'Under Executive Order No. 2, the First Deputy Mayor (Dean Fuleihan) supervises NYPD, DOC, DOF, OMB, CUNY, NYC Public Schools, and other agencies.'
    },
    {
      q: 'The Administration for Children\'s Services (ACS) falls under which Deputy Mayor?',
      choices: ['Deputy Mayor for Operations', 'Deputy Mayor for Economic Justice', 'Deputy Mayor for Health & Human Services', 'Deputy Mayor for Community Safety'],
      answer: 'Deputy Mayor for Health & Human Services',
      exp: 'ACS is part of the Health & Human Services portfolio (Helen Arteaga-Landaverde), along with H+H, DSS, DOHMH, DYCD, DFTA, and others.'
    },
    {
      q: 'Which Deputy Mayor\'s portfolio includes the Department of Transportation (DOT), the Department of Sanitation (DSNY), and FDNY?',
      choices: ['Deputy Mayor for Community Safety', 'Deputy Mayor for Operations', 'First Deputy Mayor', 'Deputy Mayor for Health & Human Services'],
      answer: 'Deputy Mayor for Operations',
      exp: 'The Deputy Mayor for Operations (Julia Kerson) oversees the agencies that keep the city running day to day -- DOT, DSNY, FDNY, DEP, DPR, DDC, DCAS, OEM, and others.'
    },
    {
      q: 'The Department of Consumer & Worker Protection (DCWP) and the Taxi & Limousine Commission (TLC) are overseen by which Deputy Mayor?',
      choices: ['Leila Bozorg, Deputy Mayor for Housing & Planning', 'Julia Su, Deputy Mayor for Economic Justice', 'Helen Arteaga-Landaverde, Deputy Mayor for Health & Human Services', 'Renita Francois, Deputy Mayor for Community Safety'],
      answer: 'Julia Su, Deputy Mayor for Economic Justice',
      exp: 'DCWP and TLC are both part of the Economic Justice portfolio (Julia Su), along with EDC, SBS, DCLA, MOME, CHR, OIA, and others.'
    }
  ];

  var form = FormApp.create(CITY_ORG_TITLE)
    .setDescription('10 questions on the structure of NYC government.\n\nSource: ' + CITY_ORG_URL)
    .setIsQuiz(true)
    .setCollectEmail(true)
    .setShuffleQuestions(false)
    .setShowLinkToRespondAgain(true)
    .setProgressBar(true)
    .setConfirmationMessage('Thanks. Check your email for your score and rank.');

  var ss = SpreadsheetApp.create(CITY_ORG_TITLE + ' Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  for (var i = 0; i < questions.length; i++) {
    var q = questions[i];
    var item = form.addMultipleChoiceItem();
    item.setTitle((i + 1) + '. ' + q.q)
      .setChoices(q.choices.map(function(c) { return item.createChoice(c, c === q.answer); }))
      .setRequired(true)
      .setPoints(1)
      .setFeedbackForCorrect(FormApp.createFeedback().setText('Correct. ' + q.exp).addLink(CITY_ORG_URL, 'Review the source').build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.exp).addLink(CITY_ORG_URL, 'Review the source').build());
  }

  form.addTextItem()
    .setTitle('Optional: enter your initials for the leaderboard')
    .setRequired(false);

  setupSheets_(ss);
  deleteExistingTrigger_('onCityOrgSubmit');
  ScriptApp.newTrigger('onCityOrgSubmit').forForm(form).onFormSubmit().create();

  Logger.log('Form URL: ' + form.getPublishedUrl());
  Logger.log('Sheet URL: ' + ss.getUrl());
}

function onCityOrgSubmit(e) {
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
    for (var j = 0; j < choices.length; j++) {
      if (choices[j].isCorrectAnswer()) { correct = choices[j].getValue(); break; }
    }
    if (String(ir.getResponse()) === correct) { score++; } else { wrong++; }
  }

  var pct = Math.round((score / CITY_ORG_TOTAL) * 100);
  var rank = getCityOrgRank(score);

  updateLeaderboard_(ss, initials, score, wrong, pct, rank.role, timestamp);

  var statsSheet = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  var cell = statsSheet.getRange(1,1);
  cell.setValue((Number(cell.getValue()) || 0) + 1);

  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: 'CB6 NYC Gov Org Chart Quiz: ' + score + '/' + CITY_ORG_TOTAL + ' -- ' + rank.role,
      body: 'CB6 NYC Government Org Chart Quiz\n\n' +
        'Score: ' + score + '/' + CITY_ORG_TOTAL + ' (' + pct + '%)\n' +
        'Rank: ' + rank.role + '\n\n' +
        rank.message + '\n\n' +
        (initials ? 'Leaderboard: ' + initials : 'No initials entered.') + '\n\n' +
        'Source: ' + CITY_ORG_URL
    });
  }
}

function setupSheets_(ss) {
  var lb = ss.getSheetByName('Leaderboard') || ss.insertSheet('Leaderboard');
  lb.clear();
  lb.getRange(1,1,1,7).setValues([['Rank','Initials','Score','Wrong','Pct','Role','Timestamp']]);
  var stats = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  stats.clear();
  stats.getRange(1,1).setValue(0);
}

function updateLeaderboard_(ss, initials, score, wrong, pct, role, timestamp) {
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

function deleteExistingTrigger_(fn) {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === fn) ScriptApp.deleteTrigger(triggers[i]);
  }
}
