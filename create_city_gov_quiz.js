/**
 * CB6 City Government & Charter Quiz
 * Run createCityGovQuiz() to build the form
 */

const CITY_QUIZ_TITLE = 'CB6 City Government & Charter Quiz';
const CITY_PAGE_URL = 'https://bkcb6.app/govhub.html';
const CITY_CORE_COUNT = 15;
const CITY_BONUS_POINTS = 1;
const CITY_LEADERBOARD_SHEET = 'Leaderboard';
const CITY_STATS_SHEET = 'Leaderboard_Stats';
const CITY_META_SHEET = 'Quiz_Meta';

function getCityRank(score, total) {
  const pct = Math.round((score / total) * 100);
  if (pct >= 95) return { role: 'Mayor', message: 'Perfect score. You could run City Hall. Keep an eye on the org chart — and maybe the ballot.' };
  if (pct >= 85) return { role: 'Deputy Mayor', message: 'You know how NYC government works at a deep level. Commissioner territory is next.' };
  if (pct >= 70) return { role: 'Commissioner', message: 'Solid grasp of the system. You understand who has power and how it gets used.' };
  if (pct >= 50) return { role: 'Deputy Commissioner', message: 'You have the foundation. Keep reading — the details matter in this city.' };
  if (pct >= 30) return { role: 'Advisor', message: 'You are learning how it works. The more you engage, the faster you will move up.' };
  return { role: 'Community Liaison', message: 'You are in the room. That is where it starts. Keep showing up.' };
}

function createCityGovQuiz() {
  const questions = [
    {
      title: 'Community boards are described as "advisory." What does that mean in practice?',
      choices: [
        'They can veto any development in their district',
        'Their recommendations are considered but not binding on decision-makers',
        'They approve the city budget',
        'They appoint agency commissioners'
      ],
      answer: 'Their recommendations are considered but not binding on decision-makers',
      explanation: 'Community boards are advisory bodies. Their votes and recommendations go into the ULURP record but do not bind the City Planning Commission, City Council, or Mayor.',
      points: 1, isBonus: false
    },
    {
      title: 'Which body has the final say on land use decisions in NYC under ULURP?',
      choices: ['The community board', 'The Mayor', 'The City Council', 'The Borough President'],
      answer: 'The City Council',
      explanation: 'Under ULURP, the City Council has final approval authority on most land use applications. The Mayor can veto, but the Council can override.',
      points: 1, isBonus: false
    },
    {
      title: 'What is "member deference" and why did the 2025 charter changes target it?',
      choices: [
        'A rule requiring CB votes to be unanimous',
        'An informal practice letting a council member effectively veto development in their district',
        'A mayoral power to override the City Council',
        'A term for seniority in Council committee assignments'
      ],
      answer: 'An informal practice letting a council member effectively veto development in their district',
      explanation: 'Member deference was the informal norm by which the full Council would defer to the local member on land use, giving any single member effective veto power. The 2025 charter changes created faster review tracks for affordable housing to limit this.',
      points: 1, isBonus: false
    },
    {
      title: 'The NYC Comptroller audits city agencies. Who elects the Comptroller?',
      choices: ['The Mayor', 'The Governor', 'New York City voters', 'The City Council'],
      answer: 'New York City voters',
      explanation: 'The Comptroller is independently elected citywide, making the office an independent check on the Mayor and city agencies.',
      points: 1, isBonus: false
    },
    {
      title: 'Which agency manages NYC\'s zoning map and runs ULURP?',
      choices: [
        'Department of Buildings',
        'Department of City Planning',
        'Landmarks Preservation Commission',
        'Office of Management & Budget'
      ],
      answer: 'Department of City Planning',
      explanation: 'DCP develops land use policy, maintains the zoning map, and manages the ULURP process. CB6 interacts with DCP on every land use application in the district.',
      points: 1, isBonus: false
    },
    {
      title: 'CB6 submitted a recommendation against a project. What happens next?',
      choices: [
        'The project is automatically rejected',
        'The applicant must withdraw',
        'The recommendation goes to the Borough President, then City Planning Commission, then City Council',
        'The Mayor makes the final call immediately'
      ],
      answer: 'The recommendation goes to the Borough President, then City Planning Commission, then City Council',
      explanation: 'Under ULURP, after the community board the application goes to the Borough President, then the City Planning Commission, then the City Council. The CB vote is one step in a multi-step process.',
      points: 1, isBonus: false
    },
    {
      title: 'The LPC designates a building as a landmark. What does that mean for the owner?',
      choices: [
        'They receive a tax exemption automatically',
        'They must get LPC approval for exterior changes',
        'The city takes ownership',
        'They can no longer sell the property'
      ],
      answer: 'They must get LPC approval for exterior changes',
      explanation: 'Landmark designation means the owner must apply to the LPC for a Certificate of Appropriateness before making changes to the exterior. CB6 has six historic districts where this applies.',
      points: 1, isBonus: false
    },
    {
      title: 'What is the Public Advocate\'s role if the Mayor dies or is removed?',
      choices: [
        'They become Mayor immediately',
        'They call a special election',
        'The Comptroller takes over',
        'They serve until the City Council elects a new Mayor'
      ],
      answer: 'They become Mayor immediately',
      explanation: 'The Public Advocate is first in the line of succession. If the Mayor leaves office, the Public Advocate becomes Mayor.',
      points: 1, isBonus: false
    },
    {
      title: 'A bar on Smith Street wants a full liquor license. Which body reviews the application before it goes to the SLA?',
      choices: [
        'Department of Consumer & Worker Protection',
        'Community Board 6',
        'Department of Buildings',
        'Department of City Planning'
      ],
      answer: 'Community Board 6',
      explanation: 'Applicants for on-premises liquor licenses must notify the local community board at least 30 days before filing with the SLA. CB6 reviews full liquor license applications and submits recommendations.',
      points: 1, isBonus: false
    },
    {
      title: 'The City Council has 51 members. How many represent CB6?',
      choices: ['One', 'Two', 'Three', 'Four'],
      answer: 'Two',
      explanation: 'CB6 is served by Council Districts 38 (Alexa Avilés) and 39 (Shahana Hanif). Community board and council district boundaries do not always align perfectly.',
      points: 1, isBonus: false
    },
    {
      title: 'What does the Department of Environmental Protection primarily do in CB6\'s context?',
      choices: [
        'Issues building permits',
        'Manages the Gowanus Canal Superfund and Red Hook CSO facility',
        'Runs NYCHA properties',
        'Oversees liquor license enforcement'
      ],
      answer: 'Manages the Gowanus Canal Superfund and Red Hook CSO facility',
      explanation: 'DEP manages water supply, wastewater, and environmental infrastructure. In CB6, DEP is directly involved in the Gowanus Canal cleanup coordination and the Red Hook combined sewer overflow facility.',
      points: 1, isBonus: false
    },
    {
      title: 'What is the difference between ELURP and standard ULURP?',
      choices: [
        'ELURP applies only to commercial projects',
        'ELURP creates faster review tracks for affordable housing projects',
        'ELURP removes community board review entirely',
        'ELURP is a state process, not a city one'
      ],
      answer: 'ELURP creates faster review tracks for affordable housing projects',
      explanation: 'The 2025 charter amendments created Expedited ULURP (ELURP) tracks — ELURP-CC and ELURP-CPC — that speed up review for qualifying affordable housing projects. Community boards still participate.',
      points: 1, isBonus: false
    },
    {
      title: 'Which elected official is first in line of succession to the Mayor?',
      choices: ['The Comptroller', 'The City Council Speaker', 'The Public Advocate', 'The Brooklyn Borough President'],
      answer: 'The Public Advocate',
      explanation: 'The Public Advocate is first in line. If both the Mayor and Public Advocate positions are vacant, the Comptroller takes over.',
      points: 1, isBonus: false
    },
    {
      title: 'What was the margin by which Brooklyn voted in favor of consolidation into Greater New York in 1894?',
      choices: ['27 votes', '277 votes', '2,770 votes', 'Brooklyn voted against it'],
      answer: '277 votes',
      explanation: 'Brooklyn voted 64,744 in favor and 64,467 opposed — a margin of just 277 votes out of more than 129,000 cast. The city we live in today was decided by 277 votes.',
      points: 1, isBonus: false
    },
    {
      title: 'The Office of Mass Engagement was created by:',
      choices: [
        'A City Council vote',
        'A charter amendment approved by voters',
        'A mayoral executive order',
        'An act of the State Legislature'
      ],
      answer: 'A mayoral executive order',
      explanation: 'On January 2, 2026, Mayor Mamdani signed an executive order creating the Office of Mass Engagement — his second day in office.',
      points: 1, isBonus: false
    },
    {
      title: 'Bonus: Which pair correctly describes the relationship between community boards and the SLA?',
      choices: [
        'Community boards approve or deny liquor licenses; the SLA handles appeals',
        'Community boards are advisory; the SLA makes the final licensing decision',
        'The SLA defers entirely to community board votes',
        'Community boards only review beer and wine licenses, not full liquor'
      ],
      answer: 'Community boards are advisory; the SLA makes the final licensing decision',
      explanation: 'Community boards review applications and submit recommendations or objections. The State Liquor Authority makes all final licensing decisions.',
      points: 1, isBonus: true
    }
  ];

  const form = FormApp.create(CITY_QUIZ_TITLE)
    .setDescription(
      'A 15-question quiz plus 1 bonus on NYC government, the City Charter, and how decisions get made.\n\n' +
      'Source: ' + CITY_PAGE_URL + '\n\n' +
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

  const spreadsheet = SpreadsheetApp.create(CITY_QUIZ_TITLE + ' Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());

  questions.forEach((q, idx) => {
    const item = form.addMultipleChoiceItem();
    const prefix = q.isBonus ? 'Bonus. ' : (idx + 1) + '. ';
    item.setTitle(prefix + q.title)
      .setChoices(q.choices.map(c => item.createChoice(c, c === q.answer)))
      .setRequired(true)
      .setPoints(q.points)
      .setFeedbackForCorrect(
        FormApp.createFeedback().setText('Correct. ' + q.explanation).addLink(CITY_PAGE_URL, 'Review the page').build()
      )
      .setFeedbackForIncorrect(
        FormApp.createFeedback().setText('Not quite. Correct answer: ' + q.answer + '. ' + q.explanation).addLink(CITY_PAGE_URL, 'Review the page').build()
      );
  });

  form.addTextItem()
    .setTitle('Optional: enter your initials for the leaderboard')
    .setRequired(false)
    .setHelpText('Leave blank if you do not want to appear on the leaderboard.');

  // Set up sheets
  const metaSheet = getOrCreateSheet_(spreadsheet, CITY_META_SHEET);
  metaSheet.clear();
  metaSheet.getRange(1,1,1,6).setValues([['Q#','Title','Answer','Explanation','Points','Bonus']]);
  questions.forEach((q,i) => metaSheet.getRange(i+2,1,1,6).setValues([[i+1,q.title,q.answer,q.explanation,q.points,q.isBonus]]));
  metaSheet.hideSheet();

  const lb = getOrCreateSheet_(spreadsheet, CITY_LEADERBOARD_SHEET);
  lb.clear();
  lb.getRange(1,1,1,9).setValues([['Rank','Initials','Score','Wrong','Pct','Bonus','Total','Role','Timestamp']]);

  const stats = getOrCreateSheet_(spreadsheet, CITY_STATS_SHEET);
  stats.clear();
  stats.getRange(1,1,2,2).setValues([['Metric','Value'],['Total Takers',0]]);

  deleteExistingTrigger_('onCityGovSubmit');
  ScriptApp.newTrigger('onCityGovSubmit').forForm(form).onFormSubmit().create();

  Logger.log('Form: ' + form.getPublishedUrl());
  Logger.log('Sheet: ' + spreadsheet.getUrl());
}

function onCityGovSubmit(e) {
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

  const stats = getOrCreateSheet_(ss, CITY_STATS_SHEET);
  const cell = stats.getRange(2,2);
  const newTotal = (Number(cell.getValue()) || 0) + 1;
  cell.setValue(newTotal);

  const pct = Math.round((coreScore / CITY_CORE_COUNT) * 100);
  const rank = getCityRank(coreScore, CITY_CORE_COUNT);

  if (initials) {
    const lb = getOrCreateSheet_(ss, CITY_LEADERBOARD_SHEET);
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
      subject: 'Your CB6 City Gov Quiz result: ' + coreScore + '/' + CITY_CORE_COUNT + ' — ' + rank.role,
      body: 'Thanks for taking the CB6 City Government & Charter Quiz.\n\n' +
        'Score: ' + coreScore + ' correct, ' + wrong + ' wrong (' + pct + '%)\n' +
        'Bonus: ' + bonusScore + '/1\n' +
        'Total score: ' + total + '/' + (CITY_CORE_COUNT + CITY_BONUS_POINTS) + '\n\n' +
        'Your rank: ' + rank.role + '\n\n' +
        rank.message + '\n\n' +
        'Total quiz takers so far: ' + newTotal + '\n\n' +
        (initials ? 'Leaderboard initials: ' + initials : 'You did not enter initials for the leaderboard.') + '\n\n' +
        'Review the source page: ' + CITY_PAGE_URL
    });
  }
}

function getOrCreateSheet_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}
function deleteExistingTrigger_(fn) {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === fn) ScriptApp.deleteTrigger(t); });
}
