/**
 * Municipal swim lesson registration — verified from city / recreation
 * commission websites on November 22, 2026. Dates are the NEXT registration
 * round after that check date (mostly Winter 2027 lessons).
 * Rule: never invent a date. Where a city has not published one, status
 * says so and the registration link is the entry point to watch.
 */

export const SWIM_CHECKED_DATE = 'November 22, 2026'

/** Soonest confirmed registration moments, chronological. */
export const SWIM_UPCOMING = [
  {
    when: 'Tue, Nov 24, 2026 · 8:30 am',
    label: 'Coquitlam — residents (winter programs incl. swimming, per the city release)',
    url: 'https://cityofcoquitlam.perfectmind.com',
    cityAnchor: 'coquitlam',
  },
  {
    when: 'Wed, Nov 25, 2026 · 9:00 am',
    label: 'Delta — residents, aquatics (swim lessons)',
    url: 'https://cityofdelta.perfectmind.com',
    cityAnchor: 'delta',
  },
  {
    when: 'Sun, Nov 29, 2026 · 9:00 pm',
    label: 'Surrey — residents, most winter programs (swim lessons follow Dec 13)',
    url: 'https://cityofsurrey.perfectmind.com',
    cityAnchor: 'surrey',
  },
  {
    when: 'Tue, Dec 1, 2026 · time to be confirmed on the city site',
    label: 'Richmond — Winter 2027 registration night (postponed from Nov 17)',
    url: 'https://www.richmond.ca/register',
    cityAnchor: 'richmond',
  },
  {
    when: 'Tue, Dec 1, 2026 · 10:00 am',
    label: 'New Westminster — residents, aquatic programs',
    url: 'https://cityofnewwestminster.perfectmind.com',
    cityAnchor: 'new-westminster',
  },
  {
    when: 'Wed, Dec 2, 2026 · 7:00 am residents / 9:00 am everyone else',
    label: 'North Vancouver (NVRC) — swimming',
    url: 'https://nvrc.perfectmind.com',
    cityAnchor: 'north-vancouver',
  },
  {
    when: 'Thu, Dec 3, 2026 · 8:00 am residents / 10:00 am everyone else',
    label: 'West Vancouver — swim & skate registration',
    url: 'https://activewestvanrec.ca',
    cityAnchor: 'west-vancouver',
  },
  {
    when: 'Fri, Dec 11, 2026 · 12:00 pm',
    label: 'Township of Langley — residents',
    url: 'https://tol.perfectmind.com',
    cityAnchor: 'township-of-langley',
  },
  {
    when: 'Sun, Dec 13, 2026 · 9:00 pm',
    label: 'Surrey — residents, aquatic programs (swim lessons)',
    url: 'https://cityofsurrey.perfectmind.com',
    cityAnchor: 'surrey',
  },
  {
    when: 'Tue, Dec 22, 2026 · 6:00 am online',
    label: 'Maple Ridge — aquatic programs (phone / in-person Dec 24, 8:00 am)',
    url: 'https://cityofmapleridge.perfectmind.com',
    cityAnchor: 'maple-ridge',
  },
]

export const SWIM_CITIES = [
  {
    id: 'delta',
    name: 'Delta',
    status: 'dated',
    next:
      'Residents — aquatics: Wed, Nov 25, 2026 at 9:00 am. Residents — other programs: Thu, Nov 26 at 9:00 am. Non-residents: Wed, Dec 9 at 9:00 am.',
    pools: ['Ladner Leisure Centre', 'Sungod Recreation Centre', 'Winskill Aquatic & Fitness Centre'],
    poolsNote: 'Outdoor pools (summer only): Ladner Outdoor Pool, North Delta Outdoor Pool.',
    registerUrl: 'https://cityofdelta.perfectmind.com',
    registerLabel: 'Register on DeltaReg (PerfectMind)',
    tips: [
      'An account is required — the city says everyone who uses Delta Parks, Recreation & Culture facilities must create one before registering.',
      'Residents get a two-week head start on aquatics (Nov 25 vs Dec 9), both at 9:00 am.',
      'Registration questions: 604-952-3000.',
    ],
    sourceName: 'City of Delta — Programs and Registration',
    sourceUrl: 'https://www.delta.ca/parks-recreation/sports-activities/programs-registration',
  },
  {
    id: 'surrey',
    name: 'Surrey',
    status: 'dated',
    next:
      'Residents — most programs: Sun, Nov 29, 2026 at 9:00 pm. Residents — aquatic programs (swim lessons): Sun, Dec 13, 2026 at 9:00 pm. Non-residents — all programs: Sun, Dec 20, 2026 at 9:00 pm.',
    pools: [
      'Surrey Sport & Leisure Complex (Fleetwood)',
      'Guildford Recreation Centre',
      'Grandview Heights Aquatic Centre',
      'South Surrey Indoor Pool',
      'Newton Recreation Centre',
    ],
    poolsNote: 'Eight outdoor pools run in summer only.',
    registerUrl: 'https://cityofsurrey.perfectmind.com',
    registerLabel: 'Register on MySurrey (PerfectMind)',
    tips: [
      'Create your MySurrey account before registration day. Surrey residents must verify their address at any recreation facility front desk (bring government ID with address) and keep a current photo on file for each family member.',
      'Virtual waiting room: log in between 8:45–8:59 pm on registration night — spots are assigned randomly at 9:00 pm, and logging in earlier gives no advantage. After 9:00 pm it is first come, first served.',
      'Waitlists are by email: if a spot opens you get 24 hours to confirm and pay, or the spot goes to the next person.',
      'Free starter lessons: Surrey residents ages 3–12 pay $0 for entry-level preschool and Swimmer 1–3 lessons (shown automatically at registration). Withdrawing within 7 days of the start date costs a $25 fee.',
      'Phone registration: 604-501-5100 (Mon–Fri, 8:30 am–4:30 pm). The city recommends Chrome.',
    ],
    sourceName: 'City of Surrey — Recreation Guide & Registration Help',
    sourceUrl: 'https://www.surrey.ca/parks-recreation/activities-registration/recreation-guide',
  },
  {
    id: 'coquitlam',
    name: 'Coquitlam',
    status: 'dated',
    next:
      'Residents: Tue, Nov 24, 2026 at 8:30 am. Non-residents: Thu, Nov 26, 2026 at 8:30 am. (City release lists these as the winter general program dates and describes a winter lineup "from swimming and skating to winter camps"; the city site does not list a separate swim-only date.)',
    pools: ['City Centre Aquatic Complex', 'Poirier Sport & Leisure Complex'],
    registerUrl: 'https://cityofcoquitlam.perfectmind.com',
    registerLabel: 'Register on SignMeUp (PerfectMind)',
    tips: [
      'You need a recreation account to register online. Check that your street address is complete and "Coquitlam" is spelled out — errors can affect resident status.',
      'Online, phone (604-927-4386) and in-person registration all open at the same time, 8:30 am.',
      'Residents register two days before non-residents.',
    ],
    sourceName: 'City of Coquitlam — Winter program registration release (Nov 13, 2026)',
    sourceUrl: 'http://www.coquitlam.ca/m/newsflash/Home/Detail/2085',
  },
  {
    id: 'port-coquitlam',
    name: 'Port Coquitlam',
    status: 'open',
    next:
      'Registration is already open: residents from Tue, Nov 17, 2026 (8:00 am), general public from Fri, Nov 20, 2026 (8:00 am). Swim lessons are part of this round; Winter 2027 classes start in January.',
    pools: ['Hyde Creek Recreation Centre', 'Port Coquitlam Community Centre (PCCC Leisure Pool)'],
    registerUrl: 'https://anc.ca.apm.activecommunities.com/cityofportcoquitlam',
    registerLabel: 'Register on ActiveNet',
    tips: [
      'Set up or update your ActiveNet account first, and use the heart icon to build a wish list — courses have been viewable since Nov 10.',
      'You can only be registered in one swim lesson set at a time, and a swimmer who is in a class cannot also sit on another set\'s waitlist. Swimmers not in a class may join multiple waitlists.',
      'Out-of-city report cards: bring them to Hyde Creek or PCCC, or email recreation@portcoquitlam.ca, so the level is on file before you register.',
      'Phone registration: 604-927-7529.',
    ],
    sourceName: 'City of Port Coquitlam — Winter 2027 registration & swimming lessons',
    sourceUrl: 'https://www.portcoquitlam.ca/our-government/media-centre/winter-2027-program-registration-begins-nov-17',
  },
  {
    id: 'richmond',
    name: 'Richmond',
    status: 'dated',
    next:
      'Winter 2027 registration night: Tue, Dec 1, 2026 (postponed from Nov 17 because of a vendor security upgrade). The city has not posted the start time yet — check the registration page before the day.',
    pools: ['Minoru Centre for Active Living', 'Watermania'],
    poolsNote: 'Outdoor pools (summer only): South Arm, Steveston.',
    registerUrl: 'https://www.richmond.ca/register',
    registerLabel: 'Register via richmond.ca/register',
    tips: [
      'Online registration needs a MyRichmond account. Before registration night, sign in once to check your login works and family birthdays are right; the city suggests a Passkey because email two-step codes can arrive late.',
      'A Queue-it virtual waiting room runs at peak times — the city says there is no need to log in early; the queue is first come, first served.',
      'Waitlists are managed by phone, so keep the phone number on your account current.',
      'Phone registration: 604-276-4300 (Mon–Fri, 8:30 am–5:00 pm). You can also register in person at any community facility.',
      'Swimmers must meet the prerequisites for the level, and a set that overlaps a class already in progress will be withdrawn by aquatics staff.',
    ],
    sourceName: 'City of Richmond — Program Registration',
    sourceUrl: 'https://www.richmond.ca/parks-recreation/registration.htm',
  },
  {
    id: 'new-westminster',
    name: 'New Westminster',
    status: 'dated',
    next:
      'Residents — aquatic programs: Tue, Dec 1, 2026 at 10:00 am. Residents — all programs: Thu, Dec 3 at 10:00 am. Everyone (incl. non-residents): Thu, Dec 10 at 10:00 am.',
    pools: ['təməsew̓txʷ Aquatic and Community Centre'],
    registerUrl: 'https://cityofnewwestminster.perfectmind.com',
    registerLabel: 'Register on PerfectMind',
    tips: [
      'New accounts need approval — the city says to expect a reply within 3 business days, so create yours well before Dec 1.',
      'Resident status must be verified: adults 19+ provide two proofs of address within 14 days of creating the account, or the account has no resident priority.',
      'A virtual waiting room runs on registration days. Full classes can be waitlisted, and the city says high-demand classes may be added.',
      'Phone registration: 604-777-5100.',
    ],
    sourceName: 'City of New Westminster — Active Living Guide (Jan–Mar 2027)',
    sourceUrl: 'https://www.newwestcity.ca/parks-and-recreation/recreation/active-living-guide-and-brochures',
  },
  {
    id: 'north-vancouver',
    name: 'North Vancouver (NVRC)',
    status: 'dated',
    next:
      'Swimming: Wed, Dec 2, 2026 — residents 7:00 am, non-residents 9:00 am. Winter courses run January–March 2027; registered lessons at the new Harry Jerome pool start the week of Jan 4.',
    pools: [
      'Delbrook Community Recreation Centre',
      'Harry Jerome Community Recreation Centre',
      'Karen Magnussen Community Recreation Centre',
      'Ron Andrews Community Recreation Centre',
    ],
    registerUrl: 'https://nvrc.perfectmind.com',
    registerLabel: 'Register on PerfectMind (NVRC)',
    tips: [
      'Virtual waiting room opens at 6:45 am. Arrive between 6:45–6:59 and your queue position is assigned randomly at 7:00; after 7:00 it is first come, first served. Do not refresh or close the tab.',
      'Check out everything in one go — spots are only held once you have paid, and registering again means rejoining the back of the queue.',
      'Browse courses from Nov 12 and note the 8-digit course IDs of your first choices. NVRC suggests Chrome.',
      'Questions: 604-987-7529.',
    ],
    sourceName: 'North Vancouver Recreation & Culture — Winter registration',
    sourceUrl: 'https://www.nvrc.ca/notices-events-blog/whats-new/get-ready-winter-registration-virtual-waiting-room-tips',
  },
  {
    id: 'west-vancouver',
    name: 'West Vancouver',
    status: 'dated',
    next:
      'Winter swim & skate registration: Thu, Dec 3, 2026 — residents 8:00 am, non-residents 10:00 am.',
    pools: ['West Vancouver Aquatic Centre (2121 Marine Dr)'],
    poolsNote: 'The Aquatic Centre is closed Nov 27–Dec 20 for annual maintenance and reopens Dec 21 — online registration on Dec 3 is not affected.',
    registerUrl: 'https://activewestvanrec.ca',
    registerLabel: 'Register on activewestvanrec.ca',
    tips: [
      'Before the day: sign in, find your classes, and tap the heart icon to save them under "Saved for Later". At 8:00 am, enrol from your list and check out.',
      'Residents get a two-hour head start. The district flags swimming and gymnastics as the fastest to fill.',
      'Full classes show "Waiting List registration is open" — join the waitlist in the system.',
      'Questions: 604-925-7270.',
    ],
    sourceName: 'District of West Vancouver — Swimming & Registration',
    sourceUrl: 'https://westvancouver.ca/parks-recreation/recreation-programs-services/recreation-activities/swimming',
  },
  {
    id: 'township-of-langley',
    name: 'Township of Langley',
    status: 'dated',
    next:
      'Courses viewable: Tue, Dec 1, 2026 at 10:00 am. Township residents: Fri, Dec 11, 2026 at 12:00 pm (noon). Non-residents (including Langley City residents): Fri, Dec 18, 2026 at 12:00 pm.',
    pools: ['Aldergrove Community Centre', 'W.C. Blair Recreation Centre', 'Walnut Grove Community Centre'],
    registerUrl: 'https://tol.perfectmind.com',
    registerLabel: 'Register on PerfectMind (Township)',
    tips: [
      'Resident priority needs a one-time address verification (in person, or the online form on the Township registration help page — allow up to 5 business days). Unverified accounts cannot use the Dec 11 resident window.',
      'One MyTownship account per household, with every family member and birthday added.',
      'A virtual waiting room runs on registration day.',
      'Waitlist: join with the green waitlist button. If a spot opens you get an email and have 36 hours to confirm or decline before it passes to the next person.',
      'One lesson set per swimmer at a time; prerequisites must be completed first.',
    ],
    sourceName: 'Township of Langley — Recreation Registration & Registration Help',
    sourceUrl: 'https://www.tol.ca/en/parks-recreation/recreation-registration.aspx',
  },
  {
    id: 'maple-ridge',
    name: 'Maple Ridge',
    status: 'dated',
    next:
      'Aquatic programs: online registration Tue, Dec 22, 2026 at 6:00 am; phone and in-person registration Thu, Dec 24, 2026 at 8:00 am. Courses can be browsed from Dec 15. (Non-aquatic programs open earlier, Dec 1 — do not mix up the dates.)',
    pools: ['Maple Ridge Leisure Centre (11925 Haney Place)'],
    poolsNote: 'Hammond Outdoor Pool is summer only.',
    registerUrl: 'https://cityofmapleridge.perfectmind.com',
    registerLabel: 'Register on PerfectMind (Maple Ridge)',
    tips: [
      'Online opens two full days before phone and in-person — that gap, not residency, is Maple Ridge\'s head start.',
      'You need a City of Maple Ridge Xplor Recreation (PerfectMind) family account.',
      'Swim lessons have level prerequisites — check the report card before choosing a class.',
      'Phone registration: 604-467-7422. In person: Maple Ridge Leisure Centre or Albion Community Centre.',
    ],
    sourceName: 'City of Maple Ridge — Programs & Registration',
    sourceUrl: 'https://www.mapleridge.ca/art-parks-rec/programs-registration',
  },
  {
    id: 'burnaby',
    name: 'Burnaby',
    status: 'rolling',
    next:
      'No single registration day for swim lessons — Burnaby runs rolling registration: residents can register 30 days before a class start date, from 10:00 am; non-residents 27 days before, from 10:00 am. Find your class start date and count back.',
    pools: [
      'Bonsor Recreation Complex',
      'CG Brown Memorial Pool',
      'Eileen Dailly Leisure Pool',
      'Edmonds Community Centre (Fred Randall Pool)',
    ],
    poolsNote: 'Outdoor pools with lessons in season: Kensington Park, MacPherson Park, Robert Burnaby. Central Park Outdoor Pool does not offer lessons.',
    registerUrl: 'https://www.burnaby.ca/WebReg',
    registerLabel: 'Register on Burnaby WebReg',
    tips: [
      'Activate your WebReg account and add classes to your Wish List ahead of your registration morning.',
      'One lesson set at a time: a swimmer must finish the current set before registering for the next, and duplicate registrations may be removed. Report cards come out on the last day of the current set.',
      'Not sure of the level? Call the facility before registering.',
      'For comparison: Burnaby\'s general winter activities open Nov 30 (residents) / Dec 4 (everyone) — but the city states swimming and skating lessons keep their rolling registration.',
    ],
    sourceName: 'City of Burnaby — Swim Lessons & winter registration news (Nov 10, 2026)',
    sourceUrl: 'https://www.burnaby.ca/recreation-and-arts/activities-and-registration/daily-activities/swim-lessons',
  },
  {
    id: 'vancouver',
    name: 'Vancouver',
    status: 'tba',
    next:
      'The Park Board has not posted a Winter 2027 swim registration date that we could verify on its website (checked Nov 22, 2026). Watch the official registration dates page and the vanrec system — and use the checklist below so you are ready the moment it appears.',
    pools: [
      'Britannia',
      'Hillcrest',
      'Kensington',
      'Kerrisdale',
      'Killarney',
      'Lord Byng',
      'Renfrew',
      'Templeton',
      'Vancouver Aquatic Centre',
    ],
    registerUrl: 'https://vanrec.ca',
    registerLabel: 'Register on vanrec (Active Communities)',
    tips: [
      'You must have an account (account holder 13+) with every child added as a family member before registration day.',
      'Build a Wish List in advance; on the day, add classes from your Wish List to the cart and check out.',
      'Register each swimmer for one lesson set only — the Park Board asks families not to hold extra spots.',
      'Waitlists are automatic: if a spot opens, the first person gets an email invitation and has 24 hours to register via the email link, by phone, or in person.',
      'You can also register in person at any Park Board facility, including centres without a pool.',
    ],
    sourceName: 'Vancouver Park Board — Registering for recreation programs',
    sourceUrl: 'https://vancouver.ca/parks-recreation-culture/registering-for-recreation-programs.aspx',
  },
  {
    id: 'port-moody',
    name: 'Port Moody',
    status: 'none',
    next:
      'No municipal swim lessons in winter — Port Moody has no indoor pool; its two outdoor pools closed for the season on Sep 6, 2026. Summer 2027 lesson dates have not been posted yet. (The city\'s Nov 24 / Nov 26 winter registration dates are for general programs, not swimming.)',
    pools: ['Rocky Point Pool (summer)', 'Westhill Pool (summer)'],
    registerUrl: 'https://cityofportmoody.perfectmind.com',
    registerLabel: 'Port Moody registration (SignMeUp)',
    tips: [
      'Create your account ahead of the summer announcement: the main contact must be 19+, and birthdays cannot be changed online afterwards.',
      'Resident priority is based on the address on the account — update it if you move.',
    ],
    sourceName: 'City of Port Moody — Aquatics',
    sourceUrl: 'https://www.portmoody.ca/parks-recreation-and-environment/recreation/aquatics/',
  },
  {
    id: 'langley-city',
    name: 'Langley City',
    status: 'none',
    next:
      'No winter swim lessons — the city\'s only pool is outdoors and reopens Apr 18, 2027. The city runs two swim registration rounds (spring and summer); the spring date has not been posted yet. (The Dec 4 winter recreation registration is for general programs, not swimming.)',
    pools: ['Al Anderson Memorial Pool (outdoor, seasonal)'],
    registerUrl: 'https://www.langleycity.ca/parks-recreation',
    registerLabel: 'Langley City recreation (ActiveNet)',
    tips: [
      'Levels are a hard requirement: a completed level must be on your account file. Report cards from other cities or the YMCA can be dropped off at Timms Community Centre or the pool, or emailed to swim@langleycity.ca.',
      'Already registered before but cannot log in? Call 604-514-2940 — the city asks you not to create a second login.',
      'One lesson set per person at a time; extra registrations are withdrawn.',
    ],
    sourceName: 'Langley City — Swimming Lessons (Al Anderson Memorial Pool)',
    sourceUrl: 'https://www.langleycity.ca/parks-recreation/recreation-facilities/al-anderson-memorial-pool/swimming-lessons',
  },
  {
    id: 'white-rock',
    name: 'White Rock',
    status: 'none',
    next:
      'No municipal swim lessons this winter — White Rock has no municipal pool, and its Winter 2027 guides list no swimming lessons. General winter program registration opened Wed, Nov 18, 2026 at 8:30 am (online, phone and in person, no resident priority).',
    pools: [],
    poolsNote: 'No municipal pool in White Rock. Nearest city pools are in Surrey (Grandview Heights Aquatic Centre, South Surrey Indoor Pool) — see the Surrey card; Surrey non-resident registration opens Dec 20 at 9:00 pm.',
    registerUrl: 'https://www.whiterockcity.ca/register',
    registerLabel: 'White Rock registration (WhiteRockREG)',
    tips: [
      'Online registration requires an account; add family members and a card in advance to check out faster.',
      'Phone registration: 604-541-2199.',
    ],
    sourceName: 'City of White Rock — Winter Recreation Guide 2027',
    sourceUrl: 'https://www.whiterockcity.ca/guide',
  },
]

/**
 * Compact table cells for the at-a-glance city table — compressed strictly
 * from the verified `next` / `tips` text above (same dates, same facts,
 * fewer words). Keyed by city id.
 */
export const SWIM_TABLE = {
  delta: {
    dates: [
      'Residents · aquatics — Wed, Nov 25, 2026, 9:00 am',
      'Residents · other programs — Thu, Nov 26, 9:00 am',
      'Non-residents — Wed, Dec 9, 9:00 am',
    ],
    tips: [
      'Account required before registering',
      'Residents get a two-week head start on aquatics',
      'Questions: 604-952-3000',
    ],
  },
  surrey: {
    dates: [
      'Residents · swim lessons — Sun, Dec 13, 2026, 9:00 pm',
      'Residents · most programs — Sun, Nov 29, 9:00 pm',
      'Non-residents · all programs — Sun, Dec 20, 9:00 pm',
    ],
    tips: [
      'Verify resident address in person (government ID); photo on file for each family member',
      'Waiting room: log in 8:45–8:59 pm — spots assigned randomly at 9:00 pm',
      'Waitlist offers by email expire in 24 hours',
      'Residents ages 3–12: entry-level lessons $0',
      'Phone: 604-501-5100',
    ],
  },
  coquitlam: {
    dates: [
      'Residents — Tue, Nov 24, 2026, 8:30 am',
      'Non-residents — Thu, Nov 26, 2026, 8:30 am',
    ],
    note: 'Winter general program dates — the city posts no separate swim-only date.',
    tips: [
      'Spell out "Coquitlam" in your account address — errors affect resident status',
      'Online, phone (604-927-4386) and in-person all open at 8:30 am',
    ],
  },
  'port-coquitlam': {
    dates: ['Open now — residents from Tue, Nov 17, 2026, 8:00 am; public from Fri, Nov 20, 8:00 am'],
    tips: [
      'Build a wish list with the heart icon (courses viewable since Nov 10)',
      'One lesson set per swimmer at a time',
      'Out-of-city report cards: drop off, or email recreation@portcoquitlam.ca',
      'Phone: 604-927-7529',
    ],
  },
  richmond: {
    dates: ['Winter 2027 registration night — Tue, Dec 1, 2026 (start time not posted yet; postponed from Nov 17)'],
    tips: [
      'MyRichmond account needed; city suggests a Passkey (email codes can arrive late)',
      'Queue-it waiting room at peak — no need to log in early',
      'Waitlists are managed by phone — keep your account phone number current',
      'Phone: 604-276-4300',
    ],
  },
  'new-westminster': {
    dates: [
      'Residents · aquatics — Tue, Dec 1, 2026, 10:00 am',
      'Residents · all programs — Thu, Dec 3, 10:00 am',
      'Everyone — Thu, Dec 10, 10:00 am',
    ],
    tips: [
      'New accounts need approval — allow 3 business days',
      'Adults 19+: two proofs of address within 14 days for resident priority',
      'Phone: 604-777-5100',
    ],
  },
  'north-vancouver': {
    dates: [
      'Residents — Wed, Dec 2, 2026, 7:00 am',
      'Non-residents — Wed, Dec 2, 2026, 9:00 am',
    ],
    tips: [
      'Waiting room opens 6:45 am; arrive 6:45–6:59 for a random queue spot at 7:00 — do not refresh',
      'Spots are held only once paid — check out in one go',
      'Note the 8-digit course IDs of your picks (browse from Nov 12)',
      'Questions: 604-987-7529',
    ],
  },
  'west-vancouver': {
    dates: [
      'Residents — Thu, Dec 3, 2026, 8:00 am',
      'Non-residents — Thu, Dec 3, 2026, 10:00 am',
    ],
    note: 'Aquatic Centre closed Nov 27–Dec 20 for maintenance (reopens Dec 21) — online registration is not affected.',
    tips: [
      'Save classes with the heart icon ("Saved for Later") before the day',
      'Swimming and gymnastics fill fastest',
      'Full class? Join the waiting list in the system',
      'Questions: 604-925-7270',
    ],
  },
  'township-of-langley': {
    dates: [
      'Residents — Fri, Dec 11, 2026, 12:00 pm',
      'Non-residents (incl. Langley City) — Fri, Dec 18, 2026, 12:00 pm',
      'Courses viewable from Tue, Dec 1, 10:00 am',
    ],
    tips: [
      'Resident priority needs one-time address verification (allow up to 5 business days)',
      'Waitlist offers by email expire in 36 hours',
      'One lesson set per swimmer at a time',
    ],
  },
  'maple-ridge': {
    dates: [
      'Online — Tue, Dec 22, 2026, 6:00 am',
      'Phone / in-person — Thu, Dec 24, 2026, 8:00 am',
      'Courses viewable from Dec 15',
    ],
    tips: [
      'Online opens two days before phone/in-person — that gap is the head start',
      'Level prerequisites apply — check the report card first',
      'Phone: 604-467-7422',
    ],
  },
  burnaby: {
    dates: [
      'Rolling — residents: 30 days before the class start date, 10:00 am',
      'Non-residents: 27 days before, 10:00 am',
    ],
    tips: [
      'Activate your WebReg account and build a Wish List ahead',
      'One set at a time — finish the current set before booking the next',
      'General winter activities (not lessons) open Nov 30 / Dec 4',
    ],
  },
  vancouver: {
    dates: ['Winter 2027 date not posted yet (checked Nov 22, 2026)'],
    tips: [
      'Account holder must be 13+; add every child before registration day',
      'Build a Wish List; on the day go Wish List → cart → pay',
      'Waitlist offers by email expire in 24 hours',
      'One lesson set per swimmer',
    ],
  },
  'port-moody': {
    dates: ['No winter swim lessons — no indoor pool (outdoor pools closed Sep 6, 2026)'],
    note: 'Summer 2027 dates not posted yet. The Nov 24 / Nov 26 winter dates are for general programs, not swimming.',
    tips: [
      'Main contact on the account must be 19+; birthdays cannot be changed online afterwards',
      'Resident priority follows the address on the account',
    ],
  },
  'langley-city': {
    dates: ['No winter swim lessons — outdoor pool reopens Apr 18, 2027; spring round not posted yet'],
    note: 'The Dec 4 winter recreation registration is for general programs, not swimming.',
    tips: [
      'Completed level must be on file; other cities\' report cards: drop off or email swim@langleycity.ca',
      'Can\'t log in? Call 604-514-2940 — do not create a second login',
      'One lesson set per person at a time',
    ],
  },
  'white-rock': {
    dates: ['No municipal swim lessons this winter — no city pool'],
    note: 'Nearest pools are in Surrey — see the Surrey row (non-residents Dec 20, 9:00 pm). General winter registration opened Nov 18, 8:30 am.',
    tips: ['Add family members and a card to your account in advance', 'Phone: 604-541-2199'],
  },
}
