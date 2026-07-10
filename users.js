// SWEAT440 Dashboard — User Access Control
// ─────────────────────────────────────────────────────────────────────────────
// Usernames are email addresses (case-insensitive at login).
// To change a password:
//   1. Open generate-hash.html in your browser
//   2. Type the new password → click Generate Hash → copy the hash
//   3. Paste it as the passwordHash below, then push to GitHub
//
// Studio names must match data.json exactly (no "SWEAT440 " prefix).
// Set studios: null for full access to all studios.
// ─────────────────────────────────────────────────────────────────────────────

const USERS = {

  // ── Admin (LeadTeam) — full access ────────────────────────────────────────
  'santiago.estrada@leadteam.com': {
    passwordHash: '32620a96dfe2cf41f26c5751dd0197ff0235421dec2bd8b3f503f187a2665c76',
    name: 'Santiago Estrada',
    studios: null,
    role: 'admin'
  },
  'santiago.estrada@sweat440.com': {
    passwordHash: '32620a96dfe2cf41f26c5751dd0197ff0235421dec2bd8b3f503f187a2665c76',
    name: 'Santiago Estrada',
    studios: null,
    role: 'admin'
  },
  'jamie.westall@leadteam.com': {
    passwordHash: 'd51efb736aca536431204927a0dc30e4909d49b809733b7ac6b1227610b6e679',
    name: 'Jamie Westall',
    studios: null,
    role: 'admin'
  },
  'sebastian.arango@leadteam.com': {
    passwordHash: '82251cee9a5262e36d13362d1b86e38fb0fb3314570ace33171d7aa3f08c33de',
    name: 'Sebastian Arango',
    studios: null,
    role: 'admin'
  },
  'daniel.jimenez@leadteam.com': {
    passwordHash: '24851852c95b5d223f697bb0a9796f93ffb7be334b3951cef647dadd61b33729',
    name: 'Daniel Jimenez',
    studios: null,
    role: 'admin'
  },
  'laura.londono@leadteam.com': {
    passwordHash: '15743531a3962a0aff9eb020754e49cb58ef8ab6ed81ddfcb674572e60c62f8a',
    name: 'Laura Londoño',
    studios: null,
    role: 'admin'
  },

  // ── Corporate (SWEAT440) — full access ────────────────────────────────────
  'matt@sweat440.com': {
    passwordHash: '92fc58cc5d4c65dc0e729ab464685f1e98ca864d367b7ead975316143eda4b98',
    name: 'Matt Miller',
    studios: null,
    role: 'corporate'
  },
  'cody@sweat440.com': {
    passwordHash: '1795997e9ff59e77d14b1539574b29538f318fc4c3f40418498810a4610db22b',
    name: 'Cody Patrick',
    studios: null,
    role: 'corporate'
  },
  'liz@sweat440.com': {
    passwordHash: 'd7e6cbbfbf54323003090f4c38df5df9cf16068d9a69d4139adfb33c1261eebb',
    name: 'Liz Schmidt',
    studios: null,
    role: 'corporate'
  },
  'valeria@sweat440.com': {
    passwordHash: '0a608db52dbac47efd7d82bbb5ca50f43d3787303323c539238b6241bcb2548c',
    name: 'Valeria Vallejo',
    studios: null,
    role: 'corporate'
  },
  'ryan@sweat440.com': {
    passwordHash: 'a55c5acee96d109db1b9dc660e624dfb0e8b5b6647b5e27797f149019897cf8e',
    name: 'Ryan Hawell',
    studios: null,
    role: 'corporate'
  },
  'scott@sweat440.com': {
    passwordHash: 'b61a400650e82386dec094ae527ad930ecfaafd2cdc9fe1a102110c6f666c3a1',
    name: 'Scott Kinsworthy',
    studios: null,
    role: 'corporate'
  },
  'ricardo@sweat440.com': {
    passwordHash: '28eb3c0cd68bbf4d712e0223ae9fd10c62c33499efc6d6d3463656ac80b670a5',
    name: 'Ricardo Martinez',
    studios: null,
    role: 'corporate'
  },
    'jose.vera@sweat440.com': {
    passwordHash: '109622880505b23e67fd78f3525ba1ecadfa8733e550c06521b738b1f87d82a2',
    name: 'Jose Vera',
    studios: null,
    role: 'corporate'
  },
  'jose@sweat440.com': {
    passwordHash: '296a0b062b2c363b5dc4264c2cc465376db6b43836be03207891ec9c78dec70b',
    name: 'Jose Vera',
    studios: null,
    role: 'corporate'
  },
  'corporate@sweat440.com': {
    passwordHash: 'ddd5c9061082705dc210837bf37f3bce4a7da96bd49915edd7ad99651d65be3b',
    name: 'SWEAT440 Corporate',
    studios: ['Miami Beach', 'Miami - Brickell'],
    role: 'corporate'
  },

  // ── Franchisees ───────────────────────────────────────────────────────────

  'alex@sweat440.com': {
    passwordHash: '32620a96dfe2cf41f26c5751dd0197ff0235421dec2bd8b3f503f187a2665c76',
    name: 'Alex Avila',
    studios: [
      'Aventura',
      'Boca Raton',
      'North Miami',
      'NYC - Chelsea',
      'NYC - FiDi',
      'NYC - Park Slope',
      'West Palm Beach',
    ],
    role: 'franchisee'
  },

  'amanda@redxfit.com': {
    passwordHash: 'd51efb736aca536431204927a0dc30e4909d49b809733b7ac6b1227610b6e679',
    name: 'Amanda Hays',
    studios: [
      'Madison',
    ],
    role: 'franchisee'
  },

  'cdevarona5@gmail.com': {
    passwordHash: '82251cee9a5262e36d13362d1b86e38fb0fb3314570ace33171d7aa3f08c33de',
    name: 'Carlos de Varona',
    studios: [
      'Miami Lakes',
      'Miramar',
      'Pembroke Pines',
    ],
    role: 'franchisee'
  },

  'chelsie@localfavorite.com': {
    passwordHash: '24851852c95b5d223f697bb0a9796f93ffb7be334b3951cef647dadd61b33729',
    name: 'Chelsie DiPaolo',
    studios: [
      'Dallas - Uptown',
    ],
    role: 'franchisee'
  },

  'vstones1430@gmail.com': {
    passwordHash: '1795997e9ff59e77d14b1539574b29538f318fc4c3f40418498810a4610db22b',
    name: 'Erika Sanchez',
    studios: [
      'Coral Gables',
      'Naples - Mercato',
    ],
    role: 'franchisee'
  },

  'gabrielzimerik@gmail.com': {
    passwordHash: 'd7e6cbbfbf54323003090f4c38df5df9cf16068d9a69d4139adfb33c1261eebb',
    name: 'Gabriel Zimeri',
    studios: [
      'Dallas - Prestonwood',
    ],
    role: 'franchisee'
  },

  'jmarcoventures@gmail.com': {
    passwordHash: '0a608db52dbac47efd7d82bbb5ca50f43d3787303323c539238b6241bcb2548c',
    name: 'Jeff Marco',
    studios: [
      'Reston',
    ],
    role: 'franchisee'
  },

  'jimmy@purefitnessmiami.com': {
    passwordHash: 'a55c5acee96d109db1b9dc660e624dfb0e8b5b6647b5e27797f149019897cf8e',
    name: 'Jimmy Kassis',
    studios: [
      'Pinecrest - Palmetto Bay',
    ],
    role: 'franchisee'
  },

  'sweat440drphillips@gmail.com': {
    passwordHash: 'b61a400650e82386dec094ae527ad930ecfaafd2cdc9fe1a102110c6f666c3a1',
    name: 'Julian Leon',
    studios: [
      'Orlando - Dr Phillips',
    ],
    role: 'franchisee'
  },

  'kenfrei212@gmail.com': {
    passwordHash: '28eb3c0cd68bbf4d712e0223ae9fd10c62c33499efc6d6d3463656ac80b670a5',
    name: 'Ken Frei',
    studios: [
      'Herriman',
    ],
    role: 'franchisee'
  },

  'kristen@sweat440eastchester.com': {
    passwordHash: '296a0b062b2c363b5dc4264c2cc465376db6b43836be03207891ec9c78dec70b',
    name: 'Kristen Albert',
    studios: [
      'Eastchester',
    ],
    role: 'franchisee'
  },

  'marcg@ubfpt.com': {
    passwordHash: 'ddd5c9061082705dc210837bf37f3bce4a7da96bd49915edd7ad99651d65be3b',
    name: 'Marc Gralnick',
    studios: [
      'Coral Springs',
      'Deerfield Beach',
      'Fort Lauderdale - Las Olas',
      'Miami - Coconut Grove',
      'Miami - Upper East Side',
      'NYC - Chelsea',
      'NYC - FiDi',
      'NYC - Park Slope',
      'Aventura',
      'North Miami',
      'Boca Raton',
      'West Palm Beach',
    ],
    role: 'franchisee'
  },

  'chris@ubfpt.com': {
    passwordHash: 'ddd5c9061082705dc210837bf37f3bce4a7da96bd49915edd7ad99651d65be3b',
    name: 'Chris Schuck',
    studios: [
      'Coral Springs',
      'Deerfield Beach',
      'Fort Lauderdale - Las Olas',
      'Miami - Coconut Grove',
      'Miami - Upper East Side',
      'NYC - Chelsea',
      'NYC - FiDi',
      'NYC - Park Slope',
      'Aventura',
      'North Miami',
      'Boca Raton',
      'West Palm Beach',
    ],
    role: 'franchisee'
  },

  'markcacciaguida@gmail.com': {
    passwordHash: '15743531a3962a0aff9eb020754e49cb58ef8ab6ed81ddfcb674572e60c62f8a',
    name: 'Mark Cacciaguida',
    studios: [
      'Doral',
      'Miami - Midtown',
    ],
    role: 'franchisee'
  },

  'matt.bvre@gmail.com': {
    passwordHash: 'd88941531023bac8a31eb314ef70f3f68384cb4d6eac6e11bcd72bfadc94857d',
    name: "Matt O'Connor",
    studios: [
      'Charlotte - Noda',
    ],
    role: 'franchisee'
  },

  'mgelrud@hotmail.com': {
    passwordHash: 'd335bf42e39a6a32a89f0af712959f8b3b99c33b7fd5d89c2eba678e53eece73',
    name: 'Max Gelrud',
    studios: [
      'South Miami',
    ],
    role: 'franchisee'
  },

  'nmarco@marcoregion.com': {
    passwordHash: 'bc791077b452b49030913ecff3162274e589a6db036dc2af28aff2c8dad78fb1',
    name: 'Nick Marco',
    studios: [
      'Middletown',
      'Ocean Township',
      'Old Bridge',
      'Toms River',
      'Wall Township',
    ],
    role: 'franchisee'
  },

  'pmarcus@catalyst-hp.com': {
    passwordHash: '852789ef58b107d14ac27bd472aa381d80d198b4ac55132799387b110bd93b76',
    name: 'Paul Marcus',
    studios: [
      'Austin - Highland',
      'Austin - Zilker',
    ],
    role: 'franchisee'
  },

  // ── Additional franchisee partners ───────────────────────────────────────

  'christina@solarisft.com': {
    passwordHash: 'b9eae662ea91a660e4d273ba7013dfa798550b66007bf87c40c5a1e638dafdaa',
    name: 'Christina',
    studios: ['Aventura', 'North Miami'],
    role: 'franchisee'
  },
  'mmasco@marcoregion.com': {
    passwordHash: '6a415abc9545d84c71b3b3bcde2848154af957d0b16418097f4af723e58412de',
    name: 'Mike Masco',
    studios: ['Reston', 'Old Bridge', 'Middletown'],
    role: 'franchisee'
  },
  'dbogota@marcoregion.com': {
    passwordHash: '8958e47f0d6c1cb275bbaa8d9d9d1e9d55e278c5144989a50e165c055dff5318',
    name: 'Danny Bogota',
    studios: ['Reston', 'Old Bridge', 'Middletown'],
    role: 'franchisee'
  },
  'jjankowski@marcoregion.com': {
    passwordHash: '40337bf924d8a08b9b27ab8c8c5229062fd2ef4ae92f6dfa3c4b7b062e1ace88',
    name: 'Joe Jankowski',
    studios: ['Reston', 'Old Bridge', 'Middletown'],
    role: 'franchisee'
  },
  'sunny@s440dfw.com': {
    passwordHash: '618f4cfb8d6a4aa6548741d58ea602bc7095b4a13b520810a5b4c3dbb28853aa',
    name: 'Sunny',
    studios: ['Dallas - Uptown'],
    role: 'franchisee'
  },
  'ron@summitfitnessgroup.com': {
    passwordHash: '837459b2dd650c83ef1d91ea46faa438cb1a6c108372b1ee122183ee6905e495',
    name: 'Ron',
    studios: ['Dunwoody'],
    role: 'franchisee'
  },
  'gretchen@summitfitnessgroup.com': {
    passwordHash: '3fcffc64c5660be7ebf4455e74d671979bd2defe63bcb92220df6f8524cbedb2',
    name: 'Gretchen',
    studios: ['Dunwoody'],
    role: 'franchisee'
  },
  'samfrei1@gmail.com': {
    passwordHash: '03af7a51f55d082887e4ae79b82bab8eb5dc6946969b6e0f7b2d43a810b358f5',
    name: 'Samantha Frei',
    studios: ['Herriman'],
    role: 'franchisee'
  },
  'jamieperucci@gmail.com': {
    passwordHash: 'e23ed7e595b5e6e135c12b79611186e5a3c95a0f784b7273928025d834986e32',
    name: 'Jamie Perucci',
    studios: ['Herriman'],
    role: 'franchisee'
  },
  'darrenperucci@gmail.com': {
    passwordHash: '9b0c94b4ec9122fa7ab056efad5514ed984b357e83a0517b8d19814e2d943183',
    name: 'Darren Perucci',
    studios: ['Herriman'],
    role: 'franchisee'
  },
  'wes@wnnen.com': {
    passwordHash: 'a43602f31f188f40319dd174550b2b7fdde97cfb2f7727aa787b625696797b87',
    name: 'Wesley',
    studios: ['Fort Myers'],
    role: 'franchisee'
  },
  'breyes887@gmail.com': {
    passwordHash: 'd2c3687b4fc174f682a88bd592ecfd03a7852a99ccb3853ea0df9c42867ce179',
    name: 'Beatriz Reyes',
    studios: ['Fort Myers'],
    role: 'franchisee'
  },
  'aron@kairosok.co': {
    passwordHash: '4fd69310ae6bd16cd698971300382cbb7deb454ba9684ff9deb191e7ae8f3e15',
    name: 'Aron',
    studios: ['OKC - Rose Creek'],
    role: 'franchisee'
  },
  'jerry.ambroise@gmail.com': {
    passwordHash: 'f62643d9cee19dd090aabc3de611ac73d552287f4176c6ba2be051a2de72c0af',
    name: 'Jerry Ambroise',
    studios: ['Long Beach'],
    role: 'franchisee'
  },
  'eileen.m.clarke@gmail.com': {
    passwordHash: 'de88d91f3bcc818a58338ed4b5695e038da471540aa3592f9c7daf1d10429974',
    name: 'Eileen Clarke',
    studios: ['Long Beach'],
    role: 'franchisee'
  },
  'william@clholdingsinc.com': {
    passwordHash: '93861ed1846a3fab6e3c88c634d3867ea7cd659cdd33a9e871a5fb965e3db697',
    name: 'William',
    studios: ['Burlington'],
    role: 'franchisee'
  },
  'douglas@clholdingsinc.com': {
    passwordHash: 'f969f537b98300ab8433e47f71df6f1e0f34cdeefc9765780ecdcdefdeb5e7cb',
    name: 'Douglas',
    studios: ['Burlington'],
    role: 'franchisee'
  },

  // ── Studio Managers (single-studio access) ───────────────────────────────

  'manager.aventura@sweat440.studio': {
    passwordHash: 'b7a17455f6ecd3263291126ae8125f00ee63b3aed9930766fecdac9c43b4d235',
    name: 'Manager Aventura',
    studios: ['Aventura'],
    role: 'manager'
  },
  'manager.boca@sweat440.studio': {
    passwordHash: 'd88941531023bac8a31eb314ef70f3f68384cb4d6eac6e11bcd72bfadc94857d',
    name: 'Manager Boca Raton',
    studios: ['Boca Raton'],
    role: 'manager'
  },
  'manager.brickell@sweat440.studio': {
    passwordHash: 'd335bf42e39a6a32a89f0af712959f8b3b99c33b7fd5d89c2eba678e53eece73',
    name: 'Manager Miami - Brickell',
    studios: ['Miami - Brickell'],
    role: 'manager'
  },
  'manager.burlington@sweat440.studio': {
    passwordHash: 'fe52a2656e8cbb762f4bdbaa37c0c4cfcce3b3364cdfde6a7a71319ff19be351',
    name: 'Manager Burlington',
    studios: ['Burlington'],
    role: 'manager'
  },
  'manager.chelsea@sweat440.studio': {
    passwordHash: 'bc791077b452b49030913ecff3162274e589a6db036dc2af28aff2c8dad78fb1',
    name: 'Manager NYC - Chelsea',
    studios: ['NYC - Chelsea'],
    role: 'manager'
  },
  'manager.coralsprings@sweat440.studio': {
    passwordHash: 'b7557e8f7e90d03a15065d11de76dbdf1100bb1e254b15c2936b4dd2fba20ad4',
    name: 'Manager Coral Springs',
    studios: ['Coral Springs'],
    role: 'manager'
  },
  'manager.dallasuptown@sweat440.studio': {
    passwordHash: 'be8e876f077d5f259efc60fe4f304f6ba81824b82090f578cc0da42377b8e5b7',
    name: 'Manager Dallas - Uptown',
    studios: ['Dallas - Uptown'],
    role: 'manager'
  },
  'manager.deerfield@sweat440.studio': {
    passwordHash: '3e7a0538eb2c216279cea5d5a7c4151da907add7f65f7b1ce8ccf47808d56497',
    name: 'Manager Deerfield Beach',
    studios: ['Deerfield Beach'],
    role: 'manager'
  },
  'manager.doral@sweat440.studio': {
    passwordHash: '152cd5b6b730da5ff307ea345f3c02e0d743f0ea50e0b37b6aaaf32ba8398caa',
    name: 'Manager Doral',
    studios: ['Doral'],
    role: 'manager'
  },
  'manager.drphillips@sweat440.studio': {
    passwordHash: '169b3d489c5f1484e5cdcf278652f9bd4c586b6207e80d66c06c3a48a1e6983e',
    name: 'Manager Orlando - Dr Phillips',
    studios: ['Orlando - Dr Phillips'],
    role: 'manager'
  },
  'manager.dunwoody@sweat440.studio': {
    passwordHash: 'c4b89ab7da4ca4a23cb04e65a81921aa3922769b8f29827e3ca762c0b74b8bce',
    name: 'Manager Dunwoody',
    studios: ['Dunwoody'],
    role: 'manager'
  },
  'manager.eastchester@sweat440.studio': {
    passwordHash: 'a84f28e657b4a9bd77c22721a234ad5ba2b1f16538abd625b805bb6bf462a911',
    name: 'Manager Eastchester',
    studios: ['Eastchester'],
    role: 'manager'
  },
  'manager.fidi@sweat440.studio': {
    passwordHash: '2f1262948495d8bd0b5fb1ce6f6f91bab2e1d1084d9dfaac63b67f44f63e26e6',
    name: 'Manager NYC - FiDi',
    studios: ['NYC - FiDi'],
    role: 'manager'
  },
  'manager.fortmyers@sweat440.studio': {
    passwordHash: '55239bb43701280ef57847f222207ee6245826f4fe16f534179c7efadd8a47bb',
    name: 'Manager Fort Myers',
    studios: ['Fort Myers'],
    role: 'manager'
  },
  'manager.gables@sweat440.studio': {
    passwordHash: '63b141a0a72671c36928eeaec0aed361d544fe7355e15b665e58e6890a1c5ec7',
    name: 'Manager Coral Gables',
    studios: ['Coral Gables'],
    role: 'manager'
  },
  'manager.grove@sweat440.studio': {
    passwordHash: '852789ef58b107d14ac27bd472aa381d80d198b4ac55132799387b110bd93b76',
    name: 'Manager Miami - Coconut Grove',
    studios: ['Miami - Coconut Grove'],
    role: 'manager'
  },
  'manager.herriman@sweat440.studio': {
    passwordHash: '7283f8e4f8a40b725e50878c74c0129861c52aef77639edb7e26ffd6c799e773',
    name: 'Manager Herriman',
    studios: ['Herriman'],
    role: 'manager'
  },
  'manager.highland@sweat440.studio': {
    passwordHash: 'ba24dc7ecc6936b16fc9119db6ccb74027fca186b09dff9f089dd1b9956ebe39',
    name: 'Manager Austin - Highland',
    studios: ['Austin - Highland'],
    role: 'manager'
  },
  'manager.lasolas@sweat440.studio': {
    passwordHash: 'f010cb846fef55667baa4ea6cd5e5a49fbc2e48280a3e3ffd39e880c2aaf7a95',
    name: 'Manager Fort Lauderdale - Las Olas',
    studios: ['Fort Lauderdale - Las Olas'],
    role: 'manager'
  },
  'manager.longbeach@sweat440.studio': {
    passwordHash: '0ab20ae17d313ec2cb6744ebedfbb864f1e0cac5c7e8cb6424cdf12a954b7372',
    name: 'Manager Long Beach',
    studios: ['Long Beach'],
    role: 'manager'
  },
  'manager.madison@sweat440.studio': {
    passwordHash: 'a79bb1122e79c261bea9b2696f7a858a802a4ae852d85d72d243cbe6217de202',
    name: 'Manager Madison',
    studios: ['Madison'],
    role: 'manager'
  },
  'manager.mercato@sweat440.studio': {
    passwordHash: '2a98e7d0c06d820a013e08eca21346c78cee4132cf0dde12d08fa931aed1b321',
    name: 'Manager Naples - Mercato',
    studios: ['Naples - Mercato'],
    role: 'manager'
  },
  'manager.miamilakes@sweat440.studio': {
    passwordHash: '5a33760b87cc73d0227fd187317a463c0a8990b139ab41342864d13553a9cce6',
    name: 'Manager Miami Lakes',
    studios: ['Miami Lakes'],
    role: 'manager'
  },
  'manager.middletown@sweat440.studio': {
    passwordHash: '1369b6c7afcc39dd730812965c81be82e7c4249b0b5780141c19d10f7a6a1620',
    name: 'Manager Middletown',
    studios: ['Middletown'],
    role: 'manager'
  },
  'manager.midtownmiami@sweat440.studio': {
    passwordHash: '4b2840986c74ab92b827c9913b66606c26ae80544320bcf217a85ba0d2ee6c47',
    name: 'Manager Miami - Midtown',
    studios: ['Miami - Midtown'],
    role: 'manager'
  },
  'manager.miramar@sweat440.studio': {
    passwordHash: '258f8cf316b2c35d89dc2cc5b76737e11affc4c040694d175fb6e0bb81d7fc87',
    name: 'Manager Miramar',
    studios: ['Miramar'],
    role: 'manager'
  },
  'manager.noda@sweat440.studio': {
    passwordHash: '946ea5c25c6f3843d3b205b5126926cacc72570af222a41de9fff829a87e920f',
    name: 'Manager Charlotte - NoDa',
    studios: ['Charlotte - Noda'],
    role: 'manager'
  },
  'manager.northmiami@sweat440.studio': {
    passwordHash: '6582d7a98ca5400aadf180126bbbb6c3433d36627b108319ffd28391901a8100',
    name: 'Manager North Miami',
    studios: ['North Miami'],
    role: 'manager'
  },
  'manager.ocean@sweat440.studio': {
    passwordHash: '8574606ea369a4a8025b7e15064dc5b1b71b7e7496e300273644351d17663ff3',
    name: 'Manager Ocean Township',
    studios: ['Ocean Township'],
    role: 'manager'
  },
  'manager.oldbridge@sweat440.studio': {
    passwordHash: 'b5dbdcaad22ae2a61af0adf47803d09eb1414d77cebdc6a818f9b78c8c114380',
    name: 'Manager Old Bridge',
    studios: ['Old Bridge'],
    role: 'manager'
  },
  'manager.parkslope@sweat440.studio': {
    passwordHash: 'ab829716343bb39cd5c80179e4f7350b492299d2b140af84fe260c95e94cb316',
    name: 'Manager NYC - Park Slope',
    studios: ['NYC - Park Slope'],
    role: 'manager'
  },
  'manager.pinecrest@sweat440.studio': {
    passwordHash: '9f8fff3e071f9fa2670a195432a9f1bed6639461b6470cb40dcc24b8afd5a44a',
    name: 'Manager Pinecrest',
    studios: ['Pinecrest - Palmetto Bay'],
    role: 'manager'
  },
  'manager.pines@sweat440.studio': {
    passwordHash: '8777b7c9cdaace4ea68c3f46c0aa27c65686b89d093e1e44581b15877d5f19bd',
    name: 'Manager Pembroke Pines',
    studios: ['Pembroke Pines'],
    role: 'manager'
  },
  'manager.prestonwood@sweat440.studio': {
    passwordHash: '6137a4244f39e374cd5cb25bfe298e1e9d73eb4348838b3fae229ee51bf9205f',
    name: 'Manager Dallas - Prestonwood',
    studios: ['Dallas - Prestonwood'],
    role: 'manager'
  },
  'manager.reston@sweat440.studio': {
    passwordHash: '74c4f3069c042afd3e585a6b3b2c6d3ddf27a88d0a4de903cfd721e206f554f3',
    name: 'Manager Reston',
    studios: ['Reston'],
    role: 'manager'
  },
  'manager.rosecreek@sweat440.studio': {
    passwordHash: 'e2030bfcb3694d4c20b9c865ad2bf0672c2ed84dc2445bf3045975c411897b4b',
    name: 'Manager OKC - Rose Creek',
    studios: ['OKC - Rose Creek'],
    role: 'manager'
  },
  'manager.sobe@sweat440.studio': {
    passwordHash: 'e8b8d515b3fc80fa44bce8bb13f3b3b0df55d6370ad994f1b60d6a51c8ea71cb',
    name: 'Manager Miami Beach',
    studios: ['Miami Beach'],
    role: 'manager'
  },
  'manager.southmiami@sweat440.studio': {
    passwordHash: '39884ad4e822a21fed7318f6b15d6ad0da092652a1e92946ff917de69151e1f0',
    name: 'Manager South Miami',
    studios: ['South Miami'],
    role: 'manager'
  },
  'manager.tomsriver@sweat440.studio': {
    passwordHash: '503a38231bd7a94edf989d4e48f1597a0959dd407a69a03445ca35d2807176ab',
    name: 'Manager Toms River',
    studios: ['Toms River'],
    role: 'manager'
  },
  'manager.uppereastside@sweat440.studio': {
    passwordHash: '566860be3de9c7b613d3706f416556ca093c5b645ce9cc009daa92ec090a636b',
    name: 'Manager Miami - Upper East Side',
    studios: ['Miami - Upper East Side'],
    role: 'manager'
  },
  'manager.wall@sweat440.studio': {
    passwordHash: '66a4e8d13343707ceb03e5a64a6cb3df045222bb3d06b9d5dee572d79c6c8370',
    name: 'Manager Wall Township',
    studios: ['Wall Township'],
    role: 'manager'
  },
  'manager.wpb@sweat440.studio': {
    passwordHash: '2143941d3794c31dc594d10e223884625f434c7abca231246263cbe0913d9196',
    name: 'Manager West Palm Beach',
    studios: ['West Palm Beach'],
    role: 'manager'
  },
  'manager.zilker@sweat440.studio': {
    passwordHash: '8b7126e0c838252809692bbc23767a5b6bc792ddc24ba55f67194e2193cf1812',
    name: 'Manager Austin - Zilker',
    studios: ['Austin - Zilker'],
    role: 'manager'
  },

};
