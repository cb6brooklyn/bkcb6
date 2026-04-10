/**
 * CB6 City Government Org Chart Quiz — 10 questions
 * Source: NYC Gov tab on govhub.html
 * Run createCityOrgQuiz() in Google Apps Script
 */

var CITY_ORG_TITLE = 'CB6 City Government Org Chart Quiz';
var CITY_ORG_URL = 'https://bkcb6.app/govhub.html';
var CITY_ORG_TOTAL = 10;

function getCityOrgRank(score) {
  var pct = Math.round((score / CITY_ORG_TOTAL) * 100);
  if (pct === 100) return { role: 'Mayor', message: 'Perfect. You know the structure cold. The org chart is in your head.' };
  if (pct >= 80)   return { role: 'Deputy Mayor', message: 'Strong command of how the city is organized. One more read and you are running a portfolio.' };
  if (pct >= 60)   return { role: 'Commissioner', message: 'You have the key pieces. A few gaps worth going back to fill.' };
  if (pct >= 40)   return { role: 'Deputy Commissioner', message: 'Solid start. The org chart is worth another pass.' };
  return           { role: 'Community Liaison', message: 'You are in the room. Keep reading — it gets clearer fast.' };
}

function createCityOrgQuiz() {
  var questions = [
    {
      q: 'The City Council has final say on land use decisions. How many members does it have?',
      choices: ['35', '45', '51', '59'],
      answer: '51',
      exp: 'The NYC City Council has 51 members. It passes local laws, adopts the budget, and has final say on land use via ULURP.'
    },
    {
      q: 'Which citywide elected official serves as first in line of mayoral succession?',
      choices: ['The Comptroller', 'The Borough President', 'The Public Advocate', 'The City Council Speaker'],
      answer: 'The Public Advocate',
      exp: 'The Public Advocate is ombudsman for New Yorkers and serves as first in line of mayoral succession.'
    },
    {
      q: 'Community boards are described on the org chart as "advisory — not binding." On what three things?',
      choices: [
        'Zoning, elections, and public safety',
        'Land use, budgets, and local services',
        'Contracts, permits, and inspections',
        'Housing, transportation, and parks'
      ],
      answer: 'Land use, budgets, and local services',
      exp: 'Community boards are advisory — not binding — on land use, budgets, and local services.'
    },
    {
      q: 'Which agency manages zoning and runs ULURP?',
      choices: [
        'Department of Buildings',
        'Department of City Planning',
        'Landmarks Preservation Commission',
        'Department of Housing Preservation & Development'
      ],
      answer: 'Department of City Planning',
      exp: 'DCP develops land use policy, manages zoning, and runs ULURP. CB6 interacts with DCP on every land use application in the district.'
    },
    {
      q: 'DEP manages water supply and wastewater. What two CB6-specific facilities are listed under DEP on the org chart?',
      choices: [
        'NYCHA Gowanus Houses and Wyckoff Gardens',
        'The Gowanus Canal Superfund and Red Hook CSO facility',
        'Prospect Park and the Columbia Street Waterfront',
        'The 76th and 78th Precincts'
      ],
      answer: 'The Gowanus Canal Superfund and Red Hook CSO facility',
      exp: 'DEP manages the Gowanus Canal Superfund and Red Hook combined sewer overflow facility — both directly relevant to CB6.'
    },
    {
      q: 'How many community boards are there citywide?',
      choices: ['51', '55', '59', '62'],
      answer: '59',
      exp: 'There are 59 community boards citywide — one or more per community district in each borough.'
    },
    {
      q: 'Which deputy mayor oversees DCP, LPC, HPD, NYCHA, and OMB?',
      choices: [
        'Deputy Mayor for Housing & Planning',
        'Deputy Mayor for Operations',
        'First Deputy Mayor',
        'Deputy Mayor for Economic Justice'
      ],
      answer: 'First Deputy Mayor',
      exp: 'The First Deputy Mayor advises the Mayor on citywide matters and oversees OMB, DOF, DCP, LPC, NYCHA, HPD, and related agencies.'
    },
    {
      q: 'LPC designates and regulates historic landmarks and districts. How many historic districts does CB6 have?',
      choices: ['Two', 'Four', 'Six', 'Eight'],
      answer: 'Six',
      exp: 'CB6 has six historic districts and reviews Certificate of Appropriateness applications with LPC.'
    },
    {
      q: 'CB6 is served by two NYPD precincts. Which are they?',
      choices: [
        '72nd and 84th Precincts',
        '76th and 78th Precincts',
        '68th and 76th Precincts',
        '78th and 84th Precincts'
      ],
      answer: '76th and 78th Precincts',
      exp: 'The 76th Precinct covers Carroll Gardens and Red Hook; the 78th Precinct covers Park Slope and Gowanus.'
    },
    {
      q: 'Borough Presidents appoint community board members. Who appoints CB6 members?',
      choices: ['The Mayor', 'The City Council', 'Antonio Reynoso', 'The CB6 Chair'],
      answer: 'Antonio Reynoso',
      exp: 'Brooklyn Borough President Antonio Reynoso appoints CB6 members with City Council input.'
    }
  ];

  var form = FormApp.create(CITY_ORG_TITLE)
    .setDescription('10 questions on the structure of NYC government — who does what and how it connects to CB6.\n\nSource: ' + CITY_ORG_URL)
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
      .setFeedbackForCorrect(FormApp.createFeedback().setText('Correct. ' + q.exp).addLink(CITY_ORG_URL, 'Review the page').build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.exp).addLink(CITY_ORG_URL, 'Review the page').build());
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
    for (var j = 0; j < choices.length; j++) { if (choices[j].isCorrectAnswer()) { correct = choices[j].getValue(); break; } }
    if (String(ir.getResponse()) === correct) { score++; } else { wrong++; }
  }

  var pct = Math.round((score / CITY_ORG_TOTAL) * 100);
  var rank = getCityOrgRank(score);

  updateLeaderboard_(ss, initials, score, wrong, pct, rank.role, timestamp);

  var statsSheet = ss.getSheetByName('Stats') || ss.insertSheet('Stats');
  var cell = statsSheet.getRange(1,1);
  var total = (Number(cell.getValue()) || 0) + 1;
  cell.setValue(total);

  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: 'CB6 City Org Quiz: ' + score + '/' + CITY_ORG_TOTAL + ' — ' + rank.role,
      body: 'CB6 City Government Org Chart Quiz\n\n' +
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
