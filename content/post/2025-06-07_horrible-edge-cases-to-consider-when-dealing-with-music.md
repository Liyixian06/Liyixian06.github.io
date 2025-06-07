---
layout:		 single
title:       "翻译｜音乐流媒体如何处理边缘问题"
subtitle:    ""
description:  " "
date:        2025-06-07T23:19:30+08:00
author: LiYixian
image:       ""
tags:        ["music", "List", "translation"]
categories:  ["Note" ]
URL: "2025/06/horrible-edge-cases-to-consider-when-dealing-with-music/"
math: False
---

原链接：[Horrible edge cases to consider when dealing with music](https://dustri.org/b/horrible-edge-cases-to-consider-when-dealing-with-music.html)   
发布日期：2022-04-02 14:45

我是 [navidrome](https://navidrome.org) 的超级粉丝，于是花了一点时间阅读它的源码，并和 [Deluan](https://deluan.com) 讨论了它的数据模型，列出了这个奇怪的边缘案例清单。

*译注：本文中的图片均为翻译时添加的；所有括号说明的内容都是译注，后面不再赘述。*

- 奇怪的专辑名称：
	- [Justice](https://en.wikipedia.org/wiki/Justice_(band)) 乐队的 [†](https://en.wikipedia.org/wiki/Cross_(Justice_album))
	- [David Bowie](https://en.wikipedia.org/wiki/David_Bowie) 的 [★](https://en.wikipedia.org/wiki/Blackstar_(album))
	- [Frank Zappa]( https://en.wikipedia.org/wiki/Frank_Zappa ) 的 ['](https://en.wikipedia.org/wiki/Apostrophe_(%27))
	- [Sigur Rós](https://en.wikipedia.org/wiki/Sigur_R%C3%B3s) 的 [()](https://en.wikipedia.org/wiki/(_)_(album))
	- 当然有 [Prince](https://en.wikipedia.org/wiki/Prince_(musician)) 的 [Love Symbol](https://en.wikipedia.org/wiki/Love_Symbol_(Prince_album))。他本人在 1993 年把自己的艺名也改成了这个符号，因此通常被称为“以前叫 Prince 的艺术家”
	
	![](https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/21/bc/80/21bc8032-fcf4-adac-9d19-2e1a6b7993ee/886448909194.jpg/1200x1200bf-60.jpg "Love Symbol 这张专辑的官方名称即为封面上这个难以发音的符号")
	
	- [Caravan Palace](https://en.wikipedia.org/wiki/Caravan_Palace) 的 [<|°_°|>](https://en.wikipedia.org/wiki/Robot_Face)
	- 微软的 Windows 和 Linux 估计都不太喜欢 [MASTER BOOT RECORD](https://masterbootrecord.bandcamp.com/) 的专辑的命名方案
  - 如果你用的是 Linux 系统，你可能会喜欢 [The You Suck Flying Circus](https://musicbrainz.org/artist/5ab0da1c-110a-416d-865d-e619db54d934) 的 [///////-//-/////](https://musicbrainz.org/release-group/75cae6b7-cd33-4e2b-9058-a7d709f7e42d)
  - 显然，蒸汽波风格的艺术家喜欢在字母之间打空格，比如 [Hallmark '87](https://hallmark87.bandcamp.com/) 的 [A T R I U M](https://hallmark87.bandcamp.com/album/a-t-r-i-u-m)
  - [Laughing Mantis](https://twitter.com/Laughing_Mantis) 发了首歌叫 [`X5O!P%@AP[4PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*`](https://open.spotify.com/track/4CutWJxNGlWTEztr1xCoS6)，也被称之为 [EICAR 反病毒测试文件](https://en.wikipedia.org/wiki/EICAR_test_file)
	
- [没有标题的专辑](https://en.wikipedia.org/wiki/List_of_untitled_musical_works)，比如 [Rammstein](https://en.wikipedia.org/wiki/Rammstein) 的  [第七张录音室专辑](https://en.wikipedia.org/wiki/Untitled_Rammstein_album)，[Led Zeppelin](https://en.wikipedia.org/wiki/Led_Zeppelin) 的  [第四张专辑](https://en.wikipedia.org/wiki/Led_Zeppelin_IV)，[KoЯn](https://en.wikipedia.org/wiki/Korn) 的 [第八张专辑](https://en.wikipedia.org/wiki/Untitled_Korn_album)，……

- 有些专辑有好几张封面：
	- [The Police](https://en.wikipedia.org/wiki/The_Police) 乐队的  [Synchronicity](https://en.wikipedia.org/wiki/Synchronicity_(The_Police_album)) 有 36 个版本的封面
	- [Art Garfunkel](https://en.wikipedia.org/wiki/Art_Garfunkel) 的 [Fate for breakfast](https://en.wikipedia.org/wiki/Fate_for_Breakfast) 有 6 个封面，但它在美国销量跳水后，大部分人只看过一个
	- [Ian Dury](https://en.wikipedia.org/wiki/Ian_Dury) 和 [The BLockheads](https://en.wikipedia.org/wiki/The_Blockheads) 的 [Do it yourself](https://en.wikipedia.org/wiki/Do_It_Yourself_(Ian_Dury_%26_the_Blockheads_album)) 至少有 34 个专辑封套
	
- 有些专辑的封面令人困惑或者[有争议](https://en.wikipedia.org/wiki/List_of_controversial_album_art)：
	- [Scorpion](https://en.wikipedia.org/wiki/Scorpions_(band)) 乐队的 [Virgin Killer](https://en.wikipedia.org/wiki/Virgin_Killer)（原版封面是一个裸体的十岁女孩）
	- [GGGOLDDD](https://gggolddd.com/) 的 [No Image](https://gggolddd.bandcamp.com/album/no-image)

	![](https://f4.bcbits.com/img/a3769570474_10.jpg)

	- [Amanda Palmer](https://en.wikipedia.org/wiki/Amanda_Palmer) 的  [There Will Be No Intermission ](https://en.wikipedia.org/wiki/There_Will_Be_No_Intermission) 封面上有她的全裸图像，并因此产生了关键部位打码的[审核版本](https://amandapalmer.bandcamp.com/album/there-will-be-no-intermission)
	- [John Lennon](https://en.wikipedia.org/wiki/John_Lennon) 和 [小野洋子](https://en.wikipedia.org/wiki/Yoko_Ono) 的 [Unfinished Music No. 1: Two Virgins](https://en.wikipedia.org/wiki/Unfinished_Music_No._1%3A_Two_Virgins)（封面是两个人的全裸照片）
	
- 令人困惑的专辑名称：
	- [The Byrds](https://en.wikipedia.org/wiki/The_Byrds) 的 [(untitled)](https://en.wikipedia.org/wiki/Untitled_(The_Byrds_album))
	- [R Kelly](https://en.wikipedia.org/wiki/R._Kelly) 的 [untitled](https://en.wikipedia.org/wiki/Untitled_(R._Kelly_album))
	- [Autechre](https://en.wikipedia.org/wiki/Autechre) 的 [untilted](https://en.wikipedia.org/wiki/Untilted)
	- [+/-](https://en.wikipedia.org/wiki/%2B/-_(band)) 乐队的 [Self-Titled Long-Playing Debut Album](https://en.wikipedia.org/wiki/Self-Titled_Long-Playing_Debut_Album) 
	- [Tintern Abbey](https://musicbrainz.org/artist/c7937ba1-6b2f-4502-9b32-df2234069a71) 的 7英寸黑胶单曲唱片的 A面（A-side）那首歌叫 [Beeside](https://musicbrainz.org/release-group/14cfbeb5-22f7-4ce9-b3ce-821aa6b30f10)
	- [Weezer](https://musicbrainz.org/artist/6fe07aa5-fec0-4eca-a456-f29bff451b04) 发行过好几张同名的 [Weezer](https://musicbrainz.org/artist/6fe07aa5-fec0-4eca-a456-f29bff451b04) 专辑，有时候一年发两次
	- [Underoath](https://en.wikipedia.org/wiki/Underoath) 发行了一张叫 [Ø (Disambiguation)](https://en.wikipedia.org/wiki/%C3%98_(Disambiguation)) 的专辑，让维基百科的  [Ø (disambiguation)](https://en.wikipedia.org/wiki/%C3%98_(disambiguation)) 页面颇为混乱
	- [Meghan Trainor](https://en.wikipedia.org/wiki/Meghan_Trainor) 的 [Title](https://en.wikipedia.org/wiki/Meghan_Trainor#2014%E2%80%932015:_Breakthrough_with_Title)
	
- 有些曲目没有标题，或名称令人困惑：
	- [Aphex Twin](https://en.wikipedia.org/wiki/Aphex_Twin) 的 [Selected Ambient Works Volume II](https://en.wikipedia.org/wiki/Selected_Ambient_Works_Volume_II)（大部分曲目都没有标题，而是使用抽象的照片或饼图表示）
	- [Mezbrow](https://musicbrainz.org/artist/2841d983-f8c3-432a-af02-7407a84580a8) 的 [Yantra Material Action](https://musicbrainz.org/release/79673a41-c5a4-4fd2-a6d7-12abaf3dc4a8)（里面每一首歌都叫 [untitled]）
	- [Autechre](https://en.wikipedia.org/wiki/Autechre) 的 [EP7](https://en.wikipedia.org/wiki/EP7#Track_listing)有一首无标题的隐藏曲目，藏在 CD 第一轨开始前的空白区域（ [pregap](https://en.wikipedia.org/wiki/Pregap)，需要从第一轨往回倒带才能听到），还有一张*正常*的曲子叫 "Left Blank"
	
- 有些曲目非常长：
	- [NǽnøĉÿbbŒrğ VbëřřĦōlökäävsŦ](http://nanocyborg.net/discog.php?i=1) 的 "Doom Apocalypse X， The Ultimate Fate Of The Universe (Part IX: The Photon Era)" 有将近 7 个小时，全专 "The Ultimate Fate Of The Universe" 接近 23 小时
	- Pipe Choir Three 的 [The Rise and Fall of Bossanova](https://en.wikipedia.org/wiki/The_Rise_and_Fall_of_Bossanova)，将一首 13 小时长的歌曲分成了 5 个部分
	- [Bull Of Heaven – 209: Blurred With Tears And Suffering Beyond Hope Bull Of Heaven - 209: Blurred With Tears And Suffering Beyond Hope](https://www.discogs.com/release/3580802-Bull-Of-Heaven-209-Blurred-With-Tears-And-Suffering-Beyond-Hope)，一首 4723 小时 54 分钟 37 秒的曲目
	
- 有些曲目非常短：
	- [Nine in Nails](https://en.wikipedia.org/wiki/Nine_Inch_Nails) 的 [Broken](https://en.wikipedia.org/wiki/Broken_(Nine_Inch_Nails_EP)) 有 99 首歌，其中第 7 首到 97 首都是 4 秒的静音
	
- 说到长度，有些专辑的名字也很长：
	- [Eximperituserqethhzebibšiptugakkathšulweliarzaxułum](https://www.metal-archives.com/bands/Eximperituserqethhzebib%C5%A1iptugakkath%C5%A1ulweliarzaxu%C5%82um/3540378310) 的 [Prajecyrujučy Sinhuliarnaje Wypramieńwańnie Daktryny Absaliutnaha J Usiopahłynaĺnaha Zła Skroź Šaścihrannuju Pryzmu Sîn-Ahhī-Erība Na Hipierpawierchniu Zadyjakaĺnaha Kaŭčęha Zasnawaĺnikaŭ Kosmatęchničnaha Ordęna Palieakantakta, Najstaražytnyja Ipastasi Dawosiewych Cywilizacyj Prywodziać U Ruch Ręzanansny Transfarmatar Časowapadobnaj Biaskoncaści Budučyni U Ćwiardyniach Absierwatoryi Nwn-Hu-Kek-Amon, Uwasabliajučy Ŭ Ęfirnuju Matęryju Prach Ałulima Na Zachad Ad Ękzapłaniety](https://www.metal-archives.com/albums/Eximperituserqethhzebib%C5%A1iptugakkath%C5%A1ulweliarzaxu%C5%82um/Prajecyruju%C4%8Dy_Sinhuliarnaje_Wypramie%C5%84wa%C5%84nie_Daktryny_Absaliutnaha_J_Usiopah%C5%82yna%C4%BAnaha_Z%C5%82a_Skro%C5%BA_%C5%A0a%C5%9Bcihrannuju_Pryzmu_S%C3%AEn%E2%80%8B-%E2%80%8BAhh%C4%AB%E2%80%8B-%E2%80%8BEr%C4%ABba_Na_Hipierpawierchniu_Zadyjaka%C4%BAnaha_Ka%C5%AD%C4%8D%C4%99ha_Zasnawa%C4%BAnika%C5%AD_Kosmat%C4%99chni%C4%8Dnaha_Ord%C4%99na_Palieakantakta%E2%80%8B.%E2%80%8B.%E2%80%8B./570638)（GPT 说这是某种伪斯拉夫语混合体，翻译成中文大概是：“通过辛-阿赫希-伊里巴的六边棱镜投射出绝对且全吞噬之恶的教义的奇点性放射，在超表面上，星座方舟的创世者将毛发技术圣殿骑士团引导至共振式未来永恒变换器的运作之中——最古老的达沃西文明化身于新-胡-凯克-阿蒙天文台的象限中，代表西方系外行星上的阿鲁利姆之尘的乙太物质”，我也不懂，随便看看吧……）
	- [Fiona Apple](https://en.wikipedia.org/wiki/Fiona_Apple) 的 [When the Pawn Hits the Conflicts He Thinks Like a King What He Knows Throws the Blows When He Goes to the Fight and He'll Win the Whole Thing 'fore He Enters the Ring There's No Body to Batter When Your Mind Is Your Might So When You Go Solo, You Hold Your Own Hand and Remember That Depth Is the Greatest of Heights and If You Know Where You Stand, Then You Know Where to Land and If You Fall It Won't Matter, Cuz You'll Know That You're Right](https://en.wikipedia.org/wiki/When_the_Pawn...)（“当兵卒卷进纷争时，他会像国王那样思考；他懂的那些东西，决定了他怎么出拳；他还没上场就已经赢了，因为他在心里早就打完了这一仗；当你的力量来自头脑，而不是拳头，根本不需要对手。所以当你独自走上前时，就握紧自己的手，记住：真正的高度来自内心的深度。如果你知道自己立足何处，也就知道什么时候该停下；就算你跌倒了，也无所谓——因为你清楚，自己没有错”）
	- [Bring me the Horizon](https://en.wikipedia.org/wiki/Bring_Me_the_Horizon) 的 [Music to Listen to\~Dance to\~Blaze to\~Pray to\~Feed to\~Sleep to\~Talk to\~Grind to\~Trip to\~Breathe to\~Help to\~Hurt to\~Scroll to\~Roll to\~Love to\~Hate to\~Learn Too\~Plot to\~Play to\~Be to\~Feel to\~Breed to\~Sweat to\~Dream to\~Hide to\~Live to\~Die to\~Go To](https://en.wikipedia.org/wiki/Music_to_Listen_To...)
	
- 曲目可以有多个创作者，比如 [GRAY (그레이) (Feat. Various Artists) - 119 REMIX](https://genius.com/Genius-english-translations-gray-feat-various-artists-119-remix-english-translation-lyrics) 有 119 个作者

- 一些乐队一直在改名字：
	- [GZR](https://en.wikipedia.org/wiki/GZR)，在他们的第一张专辑中也叫 `g//z/r`，在第二张专辑中叫 `geezer`，第三张专辑中叫 `GZR`
	- [Ghost](https://en.wikipedia.org/wiki/Ghost_(Swedish_band)) [有一段时间](https://loudwire.com/ghost-no-longer-obligated-to-use-b-c-in-name/) 叫 Ghost B.C.，但只在美国
	- [Suede](https://en.wikipedia.org/wiki/Suede_(band)) 在美国被称作 "The London Suede"
	- [Zoviet France](https://en.wikipedia.org/wiki/Zoviet_France)，也叫 ":$OVIET:FRANCE: "，"Soviet France"，": Zoviet-France: "，后者通常写作 ":zoviet\*france: "
	- [Invent, Animate](https://en.wikipedia.org/wiki/Invent_Animate) 更名为 "Invent, Animate" 以防被认作两个不同的艺术家。他们的 EP [The Sun Sleeps, As If It Never Was](https://musicbrainz.org/release/c9e98f33-cc79-4239-9b04-95323d59e4d5) 包含了三首曲目："The Sun Sleeps"，","（标题就是一个逗号）和 "As If It Never Was"
	
- 一些音乐家有很多不同的名字：
	- [Aphex Twin](https://en.wikipedia.org/wiki/Aphex_Twin)，也叫 [Blue Calx](https://www.discogs.com/artist/42476-Blue-Calx-2)（不要和 [the other Blue Calx](https://www.discogs.com/artist/41212-Blue-Calx) 搞混了），[Caustic Window](https://www.discogs.com/artist/48-Caustic-Window)，[Brian Tregaskin](https://www.discogs.com/artist/803581-Brian-Tregaskin)，[The Dice Man](https://www.discogs.com/artist/820-The-Dice-Man)，[Soit - P.P](https://www.discogs.com/artist/3671244-Soit-PP)，[Smojphace](https://www.discogs.com/artist/286337-Smojphace)，[Rutchkfard Games](https://www.discogs.com/artist/2775142-Rutchkfard-Games)，[Phonic Boy On Dope](https://www.discogs.com/artist/4101534-Phonic-Boy-On-Dope)，[Polygon Window](https://www.discogs.com/artist/2931-Polygon-Window)，[Power-Pill](https://www.discogs.com/artist/599-Power-Pill)，[Q-Chastic](https://www.discogs.com/artist/37272-Q-Chastic)，[Ricardo Jamiro](https://www.discogs.com/artist/1075022-Ricardo-Jamiro)，[Richard D. James](https://www.discogs.com/artist/435132-Richard-D-James)，[Karen Tregaskin](https://www.discogs.com/artist/829972-Karen-Tregaskin)，[GAK](https://www.discogs.com/artist/46-GAK)，[The Tuss](https://www.discogs.com/artist/798219-The-Tuss)，[user48736353001](https://www.discogs.com/artist/4229683-user48736353001) 和  [Bradley Strider](https://www.discogs.com/artist/32985-Bradley-Strider)
	- [Filipe Santos](https://www.discogs.com/artist/661099-Filipe-Santos)（此人大概有超过 150个艺名）
	
- 一些乐队的名字令人困惑：
	- [The The](https://musicbrainz.org/artist/a7409219-a681-4072-adb2-5285106ce6f2)，我猜别想再省略 "A" 或者 "The" 这种冠词了
	- 这和 [Jad and The](https://musicbrainz.org/artist/6663562b-8d36-4a55-a53e-5b433ea5023c) 里的 The 不是一回事
	- [The Band](https://en.wikipedia.org/wiki/The_Band)（“乐队”乐队）
	- [Artist Unknown](https://musicbrainz.org/artist/eb9d8589-6659-4ccc-ae9c-36cd6f95d8a8)（“艺术家未知”）
	- [Unknown Artist](https://musicbrainz.org/artist/cdf44efa-5eb1-445c-806e-fd531b2c8b5a)（“未知艺术家”）
	- [!!!](https://musicbrainz.org/artist/f26c72d3-e52c-467b-b651-679c73d8e1a7)
	- [A](https://en.wikipedia.org/wiki/A_(band))
	- 8 个叫 [Live](https://musicbrainz.org/search?query=live&type=artist&method=indexed)（现场）的乐队
	- 十几个叫 [LP ](https://musicbrainz.org/search?query=lp&type=artist&method=indexed)（正式专辑）的乐队
	
- 一些曲目故意取成令人困惑的名字，比如 [Drumkoon](https://drumkoon.bandcamp.com/) 的  [They Tried To Ban This](https://drumkoon.bandcamp.com/album/they-tried-to-ban-this) 专辑里的所有歌（都是类似于 “Hey Gugle Play The Music” 这种名字）

- 一些专辑有好几个名字：
	- Ministry 的 [Psalm 69: The Way to Succeed and the Way to Suck Eggs](https://musicbrainz.org/release-group/15cfaf82-5a4b-3ee1-bcce-75561055d27a)，这位的真名还叫 [ΚΕΦΑΛΗΞΘ](https://musicbrainz.org/release-group/15cfaf82-5a4b-3ee1-bcce-75561055d27a)
	- [The Beatles](https://en.wikipedia.org/wiki/The_Beatles_(album))，通常被称作“白色专辑”
	- [Ozzy Osbourne](https://en.wikipedia.org/wiki/Ozzy_Osbourne) 的 [Speak of the Devil](https://en.wikipedia.org/wiki/Speak_of_the_Devil_(Ozzy_Osbourne_album)) 在英国发行时的名字叫 "Talk of the Devil"
	- [Ozma](https://www.discogs.com/artist/221456-Ozma) 的 [Songs Of Inaudible Trucks And Cars](https://www.discogs.com/release/15809071-Ozma-Songs-Of-Inaudible-Trucks-And-Cars) 在上传到 MP3.com 发行时被改成了 [Songs Of Audible Trucks & Cars](https://www.discogs.com/release/8369169-Ozma-Songs-Of-Audible-Trucks-Cars)，因为字数超出了限制，无法使用完整的原始名称
	
- 大多数专辑都有好几个版本/发行版：
	- [The Eminem Show](https://musicbrainz.org/release-group/e9585ed4-d148-3711-bbee-55a97b58325a) 有 15 个版本
	- Efrim Menuck 以 [God Speed You Black Emperor!](https://musicbrainz.org/artist/3648db01-b29d-4ab9-835c-83f6a5068fe4) 的名义在 1994 年发行了磁带专辑 [All Lights Fucked on the Hairy Amp Drooling](https://musicbrainz.org/release-group/4beeac7a-57bd-4add-a611-8dc2b03c64e2)，包含 27 首曲目。该专辑 在2022 年重新发行时只包含了 4 首曲目，而非官方版本则有 31 首。哦，这支乐队还在 2002 年把名字从 "Godspeed You Black Emperor!" 改成了 "Godspeed You! Black Emperor"。
	- [Sybreed](https://en.wikipedia.org/wiki/Sybreed) 的专辑 [Antares](https://musicbrainz.org/release/909f8993-7c88-4d11-a9a7-5fba427af2e7) 日版有 12 首曲目，其中第 11 首叫 "Technocracy"，而 [美国版](https://musicbrainz.org/release/8e133ea8-5d9b-4078-a950-79a539469d10) 也有 12 首曲目，但第 11 首是 "Plasmaterial"。 [俄版](https://musicbrainz.org/release/0c42621b-5baa-4c36-b14f-896aa3143888) 和 [瑞士的宣传版](https://musicbrainz.org/release/2dc8485a-7099-40d3-8fec-97f3bfa35d83) 一样只有 11 首，而 [欧洲宣传版](https://musicbrainz.org/release/ea3f6048-71ab-465f-a9ec-b728f3130ad5) 只有 8 首。
	- [Art of Noise](https://en.wikipedia.org/wiki/Art_of_Noise) 乐队在英国发行了 4 个版本的 [Close-Up](https://www.discogs.com/release/609262-The-Art-Of-Noise-Close-Up) 单曲，这些版本都有相同的编号和封面，但曲目各不相同，其中一个版本甚至没有收录同名单曲 "Close-Up"。
	- [Taylor Swift 重新录制了她的专辑](https://en.wikipedia.org/wiki/Taylor_Swift_masters_dispute)以获得对自己音乐的完全所有权
	
- 特别烦人的版权问题：
	- [MF DOOM](https://musicbrainz.org/artist/188711ed-c99b-439c-844a-ca831f63a727) 在 2004 年发行了 [MM..FOOD](https://musicbrainz.org/release/8dc35066-e444-445a-a8c6-bb112f8bc844)，然后在 [2007 年又发了一个重新录制的版本](https://musicbrainz.org/release/2e57e853-97c4-3137-9206-8b712671a4d6)，因为其中使用了未经授权的《芝麻街》采样
	
- 不同的乐队可能会重名：
	- 以 "Emperor" 为例，它可以是：
		- [挪威黑金属乐队 Emperor](https://musicbrainz.org/artist/d9951785-7906-4daf-9a60-21753bf64aa9)
		- [鼓和贝斯制作人 Emperor](https://musicbrainz.org/artist/fffb7cb6-e9cd-42d0-81d0-60e58f13c7e8)
		- [Trance 音乐人 Emperor](https://musicbrainz.org/artist/69161e5a-51dc-473b-8a16-9007dbdbeb93)
		- [日本金属乐队 Emperor，原名 Rommel](https://musicbrainz.org/artist/9789915d-d16a-4ce8-80d3-63eda0b44e67)， 不要和日本的 [Rommel](https://musicbrainz.org/artist/da0744dd-ae58-466f-8996-ee85486bde46) 搞混
		- [《明日方舟》里的虚拟说唱歌手 Emperor](https://musicbrainz.org/artist/0130a325-81a4-4f88-b321-ccad12efe16f)
		- [说唱歌手 The Emperor](https://musicbrainz.org/artist/b0a71b2a-4c40-4aa4-b600-385fbc2a72c2)
		- [60 年代的摇滚乐队 The Emperors](https://musicbrainz.org/artist/2e29edbf-6ea4-4e96-a294-8cc634c53c30)
		- [60 年代的布鲁斯乐队 The Emperors](https://musicbrainz.org/artist/6c61b860-b243-4905-b943-eb293af10a80)
		- [90 年代的摇滚乐队 The Emperors](https://musicbrainz.org/artist/f9b03f2c-f543-4a55-b2ac-6a3e0a1ed683)
	- Havamal 可能指的是[一个维京金属乐队](https://www.metal-archives.com/bands/Havamal/3540427778)，或者，好吧，[另一个维京金属乐队](https://www.metal-archives.com/bands/H%C3%A1vam%C3%A1l/3540435790)
	- Bulldog Breed 同理，它指的可能是[一个来自英国](https://www.discogs.com/artist/442976-Bulldog-Breed-2)、出过一张专辑叫 [Made in England](https://www.discogs.com/master/179790-Bulldog-Breed-Made-In-England) 的乐队，或者[另一个来自英国](https://musicbrainz.org/artist/4385c617-664a-408a-aca7-ff45859c407d)、出过一张专辑叫 [Made in England](https://musicbrainz.org/release-group/937639bd-b48b-314f-879f-d78a16a42f3b) 的乐队
	- 以色列爵士音乐家 [Avishai Cohen](https://musicbrainz.org/artist/17d78170-7194-4603-8dbb-ca1108430882)，以及另一位以色列爵士音乐家 [Avishai Cohen](https://musicbrainz.org/artist/a9adebe6-3436-4746-bc76-3623e66f6e76)
	- 常见的“酷”名字，比如 [Revolver](https://musicbrainz.org/search?query=Revolver&type=artist&limit=100&method=indexed)，[Peace](https://musicbrainz.org/search?query=peace&type=artist&method=indexed)，[Hybrid](https://musicbrainz.org/search?query=hybrid&type=artist&method=indexed)，[End](https://musicbrainz.org/search?query=end&type=artist&method=indexed)，……
	
- 翻译问题，比如 [Пётр Ильич Чайковский (Tchaikovsky 柴可夫斯基)](https://en.wikipedia.org/wiki/Pyotr_Ilyich_Tchaikovsky)
  以及他[在 MusicBrainz 的 31 个不同的名字](https://musicbrainz.org/artist/9ddd7abc-9e1b-471d-8031-583bc6bc8be9/aliases).
  
- 一些艺术家和专辑的名字完全是在对你的 UTF-8 编码系统搞基准测试，并惹毛你的操作系统：
	- [･ ･－･ ･－ ･･･ ･ －･･](https://open.spotify.com/artist/0EUOiLsLpv9g7H9YCzUnBS) 以及他们那一吨几乎一模一样的摩斯电码单曲
	- 名字里有个[不带点的 i](https://en.wikipedia.org/wiki/Dotless_I)，还有个带 [n-元音变音](https://en.wikipedia.org/wiki/N-diaeresis) 的 [金属变音符号](https://en.wikipedia.org/wiki/Metal_umlaut) 的 [Spın̈al Tap](https://en.wikipedia.org/wiki/Spinal_Tap_(band)) 乐队
	- [⣎⡇ꉺლ༽இ•̛)ྀ◞ ༎ຶ ༽ৣৢ؞ৢ؞ؖ ꉺლ ](https://en.wikipedia.org/wiki/Four_Tet)， 还有他们那些[名字吓死人的 EP](https://en.wikipedia.org/wiki/Four_Tet_discography#EPs/Singles)（所有的 EP 和单曲的标题都由 Unicode 扩展字符集组成）。请注意，维基百科页面上的字符看上去全在往下滴水。他们也叫 [00110100 01010100](https://bleep.com/release/214740-00110100-01010100-871)， 也就是 ASCII 字符中的 "4T"。
	- [GOTO 80](https://goto8o.bandcamp.com/) 的 [Files in space](https://www.goto80.com/goto80-files-in-space-mcmp3-data-airlines) 里那些可怕的标题
	- [KEYGEN CHURCH](https://musicbrainz.org/artist/3d5635ca-6703-4f0b-b1ca-d4838e696a62) 两张名字同样重量级的专辑："░█░█░░█░█░█░" 和 "░ ▒ ▓ █"
	- [Magma](https://en.wikipedia.org/wiki/Magma_(band)) 乐队以及他们自创的 [Kobaïan](https://en.wikipedia.org/wiki/Koba%C3%AFan) 语言，有一些 UTF-8 里根本不存在的自定义变音符号
	- [Aphex Twin](https://en.wikipedia.org/wiki/Aphex_Twin) 有一首曲目叫 [∆Mᵢ⁻¹=−α ∑ Dᵢ\[η\]\[ ∑ Fjᵢ\[η−1\]+Fextᵢ \[η⁻¹\]\]](https://genius.com/Aphex-twin-formula-mi1-di-fji-1-fexti-1-lyrics)
	- [Qebrus](https://soundcloud.com/qebrus) 的 [ᐔ ᐌ ᐂ ᐍ ᐚ ](https://exophobiaorgqebrus.bandcamp.com/album/--2) 和它可怕的曲目列表。草，他[所有的音乐作品在这方面都很糟糕](https://exophobiaorgqebrus.bandcamp.com/music)。
	- [Mister Softy](https://musicbrainz.org/artist/f84c7f3c-80d9-4539-92d3-29ca02b7a57f)，更有名的名字是 `░▒▓`， 以及他的专辑 [█ ▄ █ █ ▄ ██ ▄ ██ ▄█](https://musicbrainz.org/release-group/3f6d5901-a3a1-4fb6-8d4f-0f43133a099b) 
	- [Coldplay](https://en.wikipedia.org/wiki/Coldplay) 的专辑 [Music of the Spheres](https://musicbrainz.org/release/b2de889c-6940-49ac-84be-3c0ea8733621) 使用 emoji 作为其大部分曲目的标题
	- [Flume](https://musicbrainz.org/artist/35fd8d42-b4a6-4414-9827-8766bd0daa3c) 的 [Hi This is Flume](https://musicbrainz.org/release/264dd318-2872-4a2b-bb41-bca626c70e00) 的第五首曲目
	- [Marco.V](https://www.discogs.com/artist/12236-Marco-V) 的 [C:/del*mp3](https://www.discogs.com/release/133498-MarcoV-Cdelmp3-Solarize)（在操作系统层面触碰了一堆地雷）
	- [Auto!Automatic!!](https://www.discogs.com/artist/983588-Auto!Automatic!!) 的 [Another Round Won't Get Us Down](https://www.discogs.com/master/1902714-AutoAutomatic-Another-Round-Wont-Get-Us-Down) 有一首曲目叫 \\\\\\\\\\， 还有另一首叫 //////////
	- [Ed Sheeran](https://en.wikipedia.org/wiki/Ed_Sheeran) 的四则运算专辑 [-](https://en.wikipedia.org/wiki/-_(album))， [=](https://en.wikipedia.org/wiki/%3D_(album))， [÷](https://en.wikipedia.org/wiki/%C3%B7_(album))， [x](https://en.wikipedia.org/wiki/X_(Ed_Sheeran_album)) 和 [+](https://en.wikipedia.org/wiki/%2B_(album))
	
- 古典音乐

- 我的最爱：一个叫 [brouillard](https://www.metal-archives.com/bands/Brouillard/3540375042) 的乐队，只有一个叫 brouillard 的成员，乐队的 [每张专辑](https://musicbrainz.org/artist/e217c961-ecb0-4f27-9ab7-51a031b8201b) 都叫 brouillard，当然还有每首单曲也都叫这个

 看看  [MusicBrainz 的数据库模式](https://musicbrainz.org/doc/MusicBrainz_Database/Schema) 了解要如何处理这些神经问题。
