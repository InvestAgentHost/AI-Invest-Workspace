上市公司出席人员

Michael Intrator - Co-founder, President, CEO & Chairman

机构投资者出席人员

Gabriela Borges - Goldman Sachs Group, Inc., Research Division

Presentation

Gabriela Borges Goldman Sachs Group, Inc., Research Division

All right. Fantastic. We will go ahead and kick it off on stage with the CoreWeave session at the Goldman Sachs Communacopia Conference. I'm Gabriela Borges, and I'm delighted to have Mike Intrator on stage with me, CEO of CoreWeave. Thank you for coming.

好的。非常棒。我们现在正式开始 Goldman Sachs Communacopia Conference 的 CoreWeave 专场活动。我是 Gabriela Borges，非常荣幸能邀请到 CoreWeave 的 CEO Mike Intrator 与我同台。感谢您的出席。
Michael Intrator Co-founder, President, CEO & Chairman

Excited to be here.

很高兴来到这里。
QA环节

Gabriela Borges Goldman Sachs Group, Inc., Research Division

Mike, I wanted to start with a little bit of a technical question for you, which is we've all seen the data points from third-party industry. We've, in selective cases, been able to speak with customers. And they'll consistently tell us that CoreWeave is able to deliver a level of performance on GPU training that is unparalleled in the industry. And so give us your best layman's explanation on why you think you've been able to go from a crypto miner to offering the best performance in GPU training in the industry [indiscernible].

Mike，我想先向你请教一个偏技术性的问题。我们都看到了第三方行业的数据，在某些情况下，我们也有机会与客户直接交流。他们一致表示，CoreWeave 在 GPU 训练方面所展现出的性能水平，在业内是无可匹敌的。因此，能否请你用最通俗易懂的语言为我们解释一下，你们是如何从一家加密货币挖矿企业，成功转型并提供业内顶尖的 GPU 训练性能的 [听不清]。
Michael Intrator Co-founder, President, CEO & Chairman

Sure. I'll do the best I can. So one of the things that's important to understand is when we built the company, we kind of -- we had an opportunity to kind of break it down to first principles and say, if you were going to build a cloud, specifically built to address the needs of artificial intelligence, parallelized computing, how would you go about building that? And the clear answer was you don't go about doing that by retrofitting a legacy environment to go ahead and create the solution. It's the -- like we jokingly talk about it internally, it's like the minivan versus the F1, right? It's just a -- it is a tool that was specifically built in every decision from when we founded the company in order to optimize for the specific use case, not to provide generalized computing. There are lots of great options for that.

当然。我会尽力解答。首先需要明白的重要一点是，在创立这家公司之初，我们有机会回归 first principles 来思考：如果要打造一个专门满足 artificial intelligence 和 parallelized computing 需求的 cloud，究竟该如何着手？显而易见的答案是，你不能靠修补 legacy environment 来拼凑出解决方案。就像我们在内部常开的玩笑，这好比拿 minivan 去和 F1 赛车比，不是吗？从公司成立之初的每一项决策来看，它就是一款为特定应用场景量身定制并不断优化的工具，而不是为了提供 generalized computing。毕竟在那个领域，市面上已经有许多绝佳的选择了。
And so what you have is an environment that has these compounding incremental thousands of decisions that have been built around making the environment as performant as possible for this specific use case. And we select our clients carefully in terms of finding folks that need this use case to be able to be supported and you find a software stack and infrastructure stack, all of those things really built to be able to provide that environment in the way that we do. And so it's great to hear that the clients that you're speaking to are taking advantage of the efficiencies that the tooling that we built provides them.

因此，最终呈现出的环境，是数千项微小决策不断叠加与优化的结晶，这一切皆旨在让该环境在应对这一特定的 use case 时，能够发挥出极致的性能。我们在挑选客户时也极为审慎，专门寻找那些切实需要此类 use case 支持的群体；同时，你会发现我们的 software stack 和 infrastructure stack 等一切底层架构，都是为了能以我们独有的方式来支撑这一环境而量身打造的。因此，得知您接触的客户正充分利用我们研发的 tooling 所带来的高效优势，我们感到十分欣慰。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

The next question I have for you is taking some of those performance decisions that have been made for training GPUs and then extending that advantage to something like post training and something like inference. Talk to us about why those decisions that optimize for training also give you a performance advantage for post training or for inference.

我的下一个问题是，如何将在训练 GPUs 时所做的一些性能决策，延伸并转化为 post training 和 inference 等领域的优势。请跟我们谈谈，为什么这些针对训练环节优化的决策，同样能为 post training 或 inference 带来性能上的提升。
Michael Intrator Co-founder, President, CEO & Chairman

Sure. So one of the things that we kind of believed very early on was that the space was going to evolve very, very quickly. And when you're in an environment as dynamic as that, you want to build your infrastructure to have the most amount of optionality embedded in it as possible, right? And so we don't really think about our infrastructure as being, oh, this is our training infrastructure, and this is our inference infrastructure. We think of it as AI infrastructure. And we build to a standard that allows our clients to use that infrastructure in whatever way they deem to be most productive for their businesses, and that's how we built it.

当然。我们在极早期就确信一点，即该领域的演进速度将异常迅猛。置身于如此瞬息万变的环境中，你必然希望在构建基础设施时，赋予其最大程度的灵活性，对吧？因此，我们不会将基础设施刻板地划分为，哦，这是我们的 training 基础设施，那是我们的 inference 基础设施。我们将其统称为 AI 基础设施。我们致力于确立一种标准，让客户能以最有利于自身业务发展的方式来利用这些基础设施，这正是我们的构建之道。
And so all of the tooling that we have within our Mission Control and all the other observability suites and all the tooling that we have provides for an environment that allows for incredibly performant environment for folks that are using the compute. And we can see when people are using it in different ways, the consumption profile will look different. All of those things will follow with their use case. But to varying degrees, different parts of our stack will provide for different advantages depending upon what their use case is.

因此，我们在 Mission Control 及其他所有 observability suites 中配备的各类工具，共同构建了一个基础环境，为使用 compute 的用户提供了极其卓越的性能体验。我们也注意到，当用户的操作方式发生变化时，其 consumption profile 也会呈现出不同的特征。这一切都取决于他们具体的 use case。不过，根据 use case 的不同，我们 stack 的各个组成部分将在不同程度上展现出各自的独特优势。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

This all makes sense. I want to pick your brain on a couple of industry dynamics that we get asked about all the time that are very core to where CoreWeave sits in the stack. So the first one is supply-demand, where CoreWeave has consistently said that we might not be at supply-demand equilibrium until the end of the decade. And so my question to you is tell us a little bit more about how the demand environment has evolved this year because of agentic? And where do you think it goes from here? What do you think is being underappreciated about agentic demand over the next 12 months?

这完全说得通。我想向您请教几个我们经常被问及的行业动态，这些动态与 CoreWeave 在技术栈中的核心地位息息相关。首先是供需问题，CoreWeave 始终表示，我们可能要到本年代末才能实现供需平衡。因此我想请问，能否详细谈谈今年 agentic 的出现是如何改变需求环境的？您认为未来趋势将走向何方？在未来12个月内，您认为市场对 agentic 需求的哪些方面认识不足？。
Michael Intrator Co-founder, President, CEO & Chairman

Yes. So the -- we have been incredibly consistent in the way that we talk about demand. And that has been driven by our ability to talk to an incredible cross-section of compute consumers, right? And that's everything from the hyperscalers through the AI native, the frontier labs, people that are productizing and delivering agentic solutions, all of those things. And we have never flinched from our assessment that the world's capacity to deliver compute has been and will continue to be wildly overwhelmed by the delivery and demand for intelligence, broadly speaking. And so we've been righter than wrong on that one. And I've got a bunch of really smart folks around me that come in and yell at me every day that we don't have enough compute. So I'll take their word for it.

是的。我们在谈及需求时的口径始终高度一致。这得益于我们能够与极其广泛的 compute 客户群进行深入交流，不是吗？这个群体涵盖了 hyperscalers、AI native 企业、frontier labs，以及致力于将 agentic solutions 产品化并推向市场的开发者等方方面面。我们始终坚信一项评估，即从宏观来看，全球提供 compute 的能力过去是、未来也将继续被对 intelligence 的巨大需求和交付量远远甩在身后。事实证明，我们在这一点上的判断大体是准确的。我身边有一大批绝顶聪明的人，他们每天都跑来向我疾呼我们的 compute 严重不足。对此，我深信不疑。
The -- one of the really interesting, I'm not sure this exactly answers your question, but one of the really interesting phenomenon that you're seeing in the market right now is the large consumers of our services of compute delivery of the software stack that we've built on top of that. Those consumers are demanding ever larger amounts of resources, right? It's -- every -- we have the 9-month rule at CoreWeave. We look back at whatever we've done and we -- 9 months later, we think it's cute. And that's kind of how we've -- that's the dynamic that we've seen in the market. But that is being compounded right now because of new entrants into the market. And new entrants are enterprise clients coming in. And I talked about this a little bit on my last earnings call where a company like Caterpillar comes and starts to use us. And it's a great example of enterprise consumer coming to us and saying, hey, the way that we're going to participate with our company in artificial intelligence, the way that we're going to train our models, the way that we're going to serve our models is going to look different than it has historically. We're going to build our own clusters. And that is transformational, right? That is really allowing CoreWeave to establish itself as an AI cloud participant, a hyperscaler within the AI system. And that's been really, really exciting for us.

这——其中一个非常有趣的现象，我不确定这是否完全回答了你的问题，但你现在在市场上看到的一个非常有趣的现象是，我们计算交付服务以及基于此构建的软件栈的大型消费者。这些消费者对资源的需求正变得越来越大，对吧？这是——每一个——我们在 CoreWeave 有一个9个月法则。每当我们回首过去所做的一切，我们——9个月后，都会觉得当时的规模不值一提。这就是我们如何——这就是我们在市场上观察到的动态。但随着新参与者涌入市场，这种趋势目前正在加剧。这些新参与者正是不断涌入的企业客户。我在上一次财报电话会议上也曾略微提及，像 Caterpillar 这样的公司已经开始使用我们的服务。这是一个绝佳的例子，企业消费者找到我们并表示，嘿，我们公司参与人工智能的方式，我们训练模型的方式，我们提供模型服务的方式，都将与以往截然不同。我们将构建自己的集群。这具有变革性的意义，对吧？这真正使得 CoreWeave 能够确立自己作为 AI 云参与者的地位，成为 AI 生态系统中的一家 hyperscaler。这对我们而言无疑是极其令人振奋的。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

I'm curious what you think changed that now has enterprise customers wanting to build their own AI clusters in-house versus outsourcing?

我很好奇，您认为究竟发生了什么转变，使得现在的企业客户更倾向于在内部自建 AI clusters，而不是选择外包？
Michael Intrator Co-founder, President, CEO & Chairman

I think it's a lot of things. I think part of it is the experience of building cloud-based systems over the past 20 years has given companies some perspective about how important compute was going to be. And then with the advent of artificial intelligence and the degree to which that kind of raises the stakes, there is an interest in having more control over that resource that they consider to be fundamental and important to their businesses than perhaps they did historically. It's the boiled lobster problem, right? It's like the cloud kind of came out of nowhere and people began to use it and people were using it before they realized how incorporated and embedded it was going to be within their critical systems.

我认为这背后有多重原因。部分原因在于，过去20年构建 cloudbased systems 的经验，让企业深刻预见到了 compute 的重要性。此外，随着 artificial intelligence 的到来及其带来的更高竞争筹码，企业开始将这种资源视为业务的重中之重，因此比以往任何时候都更渴望加强对它的控制。这就是温水煮青蛙的困境，对吧？cloud 仿佛横空出世，人们顺理成章地开始使用它，而在意识到它将如何与关键系统深度融合并嵌入其中之前，人们就已经深陷其中了。
And this time, they're going in with eyes wide open, which really provides us with a wonderful opportunity to go to them and say, hey, we can really assist you beyond what has been an oligopoly of 3 massive companies that have delivered this service. We have some alternatives. We have a different way of looking at it. We have a different way of providing the compute that will be most performant to you. And that drives down cost. It does all kinds of great things for you.

这一次，他们对局势有着清醒的认识，这无疑为我们创造了绝佳的契机。我们可以主动找到他们并表明：嘿，长期以来，这项服务一直被3家巨头寡头垄断，而我们能在此之外为您提供真正的助力。我们拥有其他的替代方案，也有着截然不同的视角。我们能以全新的方式，为您提供性能最优的 compute。这不仅能大幅削减成本，还能为您带来诸多切实的好处。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Very good. Okay. So my second industry question is world models. When do you think world models start to have an impact on the demand curve to CoreWeave? And I know you've already announced customers in this space.

很好。好的。那么我的第二个行业问题是关于 world models 的。您认为 world models 何时会开始对 CoreWeave 的需求曲线产生影响？我知道贵公司已经公布了该领域的客户。
Michael Intrator Co-founder, President, CEO & Chairman

Yes. So look, it's the same but different is the way I look at that. The value propositions that a company like CoreWeave provide to that space are really quite similar to the value propositions that we provide across the entire space. Yes, their data is a little different. All of those things are true. But I do think that really when you're thinking about the world models or agentic, like it really comes down to have you built your infrastructure, have you built the software rails and the stack to provide an environment that is going to be incredibly performant, incredibly well controlled, incredibly cost effective from the amount of compute that you're able to squeeze out of every dollar you invest. And all of those things are -- that is the North Star for CoreWeave. It's how we built our business from day 1.

是的。在我看来，这其实是大同小异。像 CoreWeave 这样的公司为该垂直领域提供的价值主张，与我们为整个行业提供的价值主张其实高度一致。诚然，他们的数据略有不同，这些都是事实。但我始终认为，当你在探讨 world models 或 agentic 时，核心问题在于：你是否搭建了完善的基础设施？是否构建了相应的软件架构与 stack，从而打造出一个具备极致性能、高度可控且极具成本效益的运行环境——即让你投资的每一美元都能发挥出最大的算力价值。所有这一切，正是 CoreWeave 始终笃行的 North Star。这也是我们自创立第一天起就秉持的商业构建之道。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

We're about to go into midterm elections here, and we've seen on both sides of the aisle, a number of debates around data centers that, in aggregate, have made ease of scaling and securing a data center harder than it was a year ago or 2 years ago. How do you navigate at CoreWeave, the stuff that's within your control? How do you plan for what's not in your control? Where do you think this debate goes over the next year?

随着中期选举临近，我们看到两党围绕 data centers 展开了诸多辩论。总体而言，与一两年前相比，这些争议使得 data center 的规模扩张与安全保障变得更加困难。在 CoreWeave，你们如何处理那些可控的因素？又如何应对那些不可控的变数？你认为未来一年这场辩论将走向何方？。
Michael Intrator Co-founder, President, CEO & Chairman

Okay. So somehow in a relatively short period of time, I turned into a bad guy according to my son because of the data center dialogue that's out there. Look, we have a method and approach to how you go about building and scaling data center capacity that is really built around entering the markets early, really working with the local communities, being sensitive to their needs and building infrastructure that is useful to our clients while not being unreasonably irritating to the local communities. And that has been a very productive way to approach building infrastructure.

好吧。不知怎的，在相当短的时间里，因为外界关于 data center 的种种议论，在我儿子眼里我竟然成了一个坏人。听着，在建设和扩展 data center 规模方面，我们有一套自己的方法与策略，其核心在于及早进入市场，切实与当地社区合作，体察他们的需求，从而在为客户建设实用基础设施的同时，不至于给当地社区带来无谓的困扰。事实证明，这是一种非常高效的基础设施建设模式。
The world is definitely evolving, right? There is increased resistance to data centers going into communities. There are pieces of that debate that I think are completely nonsense, and I think there are pieces of the debate that are -- that warrant real introspection by the industry. And so water usage, these are closed-loop systems. And as more of the data centers come online that are able to support this AI infrastructure that is so power-intensive, they must be closed-loop systems. They don't function unless they are. And so I think that it is at a -- going into the elections, it's going to be a maximum volume. I think that the approach of not allowing data centers to be built is kind of a fool's errand in some ways because I think the demand for the compute doesn't change. It just moves in terms of where it's going to be built and how much it's going to cost to build. But I don't think it changes the overarching demand cycle.

毫无疑问，世界正在不断演变，对吧？数据中心入驻社区正面临越来越大的阻力。在这场争论中，我认为有些观点纯属无稽之谈，但也有一些声音确实值得整个行业进行深刻反思。以用水量为例，这些设施采用的是闭环系统。随着越来越多能够支撑高耗能 AI 基础设施的数据中心投入运营，它们必须采用闭环系统。否则它们根本无法运转。因此我认为，随着选举临近，这种争议的声量将达到顶峰。在我看来，试图阻止数据中心建设的做法在某种程度上是徒劳的，因为对算力的需求并未改变。改变的仅仅是建设地点和建造成本。但这并不会改变宏观的需求周期。
We have been really, really forward thinking around the idea of diversifying our portfolio of data center infrastructure. And once again, I talked a little bit about this on my earnings call because it's such an incredibly high-profile issue. But like I talked about the idea that we have over 1 gigawatt of power contracted outside of the U.S. as you kind of look to build a portfolio of infrastructure to be able to support your clients with. And I think that's the right strategy, and I think we'll continue to kind of focus on making sure that we can build both within the domestic U.S. but abroad as well.

在推动数据中心基础设施组合多元化方面，我们的目光一直非常长远。由于这是一个备受瞩目的核心议题，我在 earnings call 中再次提及了这一点。正如我之前谈到的，我们在 U.S. 境外已经签署了超过1 gigawatt 的电力合同，因为我们需要构建完善的基础设施组合来为客户提供支持。我认为这一战略是正确的，未来我们也将继续致力于确保在 U.S. 国内及海外市场同步推进建设。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Maybe I can bridge this to a horizontal and vertical integration question. So we'll talk a little bit more about your ability to go up into the software stack. What I want to ask you is why now you feel the need to also own the underlying data centers. I think you have your first data center coming online by the end of this year. What's driving that decision on vertical integration beyond the margin stacking argument?

或许我可以顺势引出一个关于水平与垂直整合的问题。接下来，我们将进一步探讨贵公司向软件栈上层拓展的能力。我想请问的是，为何您认为现在有必要自主掌控底层的数据中心。据我所知，贵公司的首座数据中心将于今年年底前投入运营。除了利润叠加的逻辑之外，究竟是什么促使你们做出了这一垂直整合的决定？。
Michael Intrator Co-founder, President, CEO & Chairman

So this is not a new issue for us. We've thought a lot about this. We've spent a lot of time thinking about which parts of the vertical integration we want to be involved with. There are 2 reasons that you want to vertically integrate downward. And both of them are very important. The first one is that by vertically integrating down into the physical data centers, you can recapture some margin, right? And I would say that's the lesser of the 2.

因此，这对我们而言并非新课题。我们对此进行过深思熟虑，也投入了大量时间来权衡究竟该涉足 vertical integration 的哪些环节。企业选择向下进行 vertical integration 通常出于两个原因，且两者都至关重要。首先，通过向下 vertical integration 延伸至实体 data centers，企业能够收回部分 margin，不是吗？不过我认为，在这两个原因中，这还算是次要的。
The second thing is this stuff is difficult, right? It's not, hey, I've got some megawatts and I'm going to turn that into a supercomputer. There's a lot of steps along the way there. And entering into an environment where we have more control, a deeper understanding, a better sandbox to work on the flywheel of new innovations that we want to bring to our own data centers, that makes us stronger, right? More control over pieces of our infrastructure make us better. And so it's not a new part of our strategy. We've thought a lot about it.

其次，这类工作本身难度极高，不是吗？这绝非“嘿，我手头有几兆瓦的电力，就能直接把它变成一台超级计算机”那么简单。这中间需要跨越繁复的步骤。此外，进入一个我们能施加更多控制、具备更深理解的环境，并获得一个更优质的沙盒，以此来推动我们希望引入自家数据中心的创新飞轮，这无疑会增强我们的实力，对吧？对基础设施各个环节把控力的提升，会让我们变得更优秀。因此，这并非我们战略中的临时起意。对此我们早已深思熟虑。
Data centers take time to build. And so you're starting to see the first 2 or 3 of our self-builds spin up, which we're incredibly excited about. But you will see a continued effort on our part to control the physical infrastructure, both up and down the stack. We think it's important. We think control is important, learning is important.

数据中心的建设非一日之功。因此，大家现在才开始看到我们首批两三个自建项目正式投入运行，这令我们无比振奋。不过，未来各位将看到我们持续发力，力求实现对物理基础设施的全面掌控，贯穿整个 stack 的各个层级。我们深知其重要性。在我们看来，掌控力至关重要，从中不断学习同样不可或缺。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Let me stay on this point on bringing more capacity online is very hard operationally to do. We've seen so many announcements from new entrants in the past several months where we'll get data points on companies bringing on 10 gigawatts over the next 2 years, 7 gigawatts over the next 2 years. How do you think this all shakes out from an industry structure standpoint?

让我继续探讨刚才那一点：在实际操作中，新增产能的落地可谓困难重重。过去几个月，我们看到众多新入局者频频发布公告，其中不乏一些公司计划在未来两年内新增 10 gigawatts 或 7 gigawatts 产能的具体数据。从行业结构的角度来看，您认为这最终会引发怎样的行业洗牌？。
Michael Intrator Co-founder, President, CEO & Chairman

I think it's hard. I think building infrastructure is difficult. I think that some will be more successful than others. I think that it is a capital-intensive industry and capital-intensive industries will tend towards periods of proliferation and they will tend towards periods of consolidation. I think that during a time where the demand is so incredibly overwhelming, it is easier to launch a company.

我认为这绝非易事。基础设施建设困难重重。必然会有一些企业比其他企业更为成功。这是一个资本密集型产业，而此类产业往往会交替经历扩张期与整合期。在当前需求如此旺盛的时期，创立一家公司相对而言要容易得多。
But the difference between launching a company and talking about a contract you signed and actually being able to operationalize and deliver and maintain that infrastructure, the more experience you have with it, the more you realize how difficult it is to do over time. And so I think there's going to be some interesting outcomes that are going to be associated with delivering this new infrastructure.

但是，创办公司或大谈签下的合同是一回事，而真正将基础设施落地、交付并长期维护则是另一回事。在这个领域经验越丰富，就越能体会到长期执行的艰巨性。因此我认为，在交付这些全新基础设施的过程中，我们将会看到一些耐人寻味的结局。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Absolutely. Okay. Let me ask you the supply-demand question in a slightly different way. So we've established that we're in a period of incredible supply constraints. At some point, and we can debate when that is, the industry will come back into supply-demand balance. Right now, CoreWeave gives us these amazing data points on contract renewals for H100s and pricing dynamics. How should we think about longer term, what happens when supply-demand normalizes? And the bear case we hear from investors all the time is, well, you have hyperscaler customers who can simply then pull back what they've 'outsourced' to CoreWeave and retrench back in the stack. And so maybe just would love your thoughts on the longer term for CoreWeave in a normalized supply-demand environment.

没问题。好的。让我换个角度来探讨一下供需问题。我们已经达成共识，当前正处于供应极度受限的时期。尽管具体时间尚可商榷，但行业终将在某个节点回归供需平衡。眼下，CoreWeave 在 H100s 的合同续签和定价动态方面，为我们提供了非常亮眼的数据。但把目光放长远来看，当供需关系恢复正常时会发生什么？我们经常听到投资者提出一种悲观的假设：那些 hyperscaler 客户届时完全可以把“外包”给 CoreWeave 的业务收回，并重新收缩回自己的 stack 中。因此，我很想听听您对 CoreWeave 在供需常态化环境下的长期发展有何见解。
Michael Intrator Co-founder, President, CEO & Chairman

So I think my last answer is the most like politically correct answer I could have given to that question. Look, CoreWeave has been leading the AI cloud space now since its inception. I would argue that largely CoreWeave has really built the space. What started out as a cost-plus environment where we were able to win contracts because we would go to large consumers of compute and say, hey, we'll build this for you and they would say, well, we're willing to pay cost-plus for it. That kind of built our business and allowed us to scale. And with scale in this business comes all kinds of incredible ways of driving economics and driving margin, which we're really excited about, and the market will see that continue to accrete to us over time.

所以，我认为我刚才的回答，已经是针对该问题最政治正确的答复了。毫无疑问，CoreWeave 自创立伊始便一直领跑 AI cloud 领域。我甚至认为，在很大程度上，正是 CoreWeave 一手开创了这一领域。早期这是一个 costplus 的市场环境，当时我们之所以能拿下合同，是因为我们会主动找到 compute 的大客户，提出，嘿，我们可以为你们搭建这个，而对方则会回应，很好，我们愿意以 costplus 的模式买单。正是这种模式奠定了我们的业务基础，并使我们得以实现规模化扩张。而在这一行业，规模化会带来各种不可思议的手段来优化经济效益和提升 margin，对此我们感到无比振奋，市场也将见证，随着时间的推移，这些优势会源源不断地向我们汇聚。
The other piece of it is just these companies, they entered into contracts with us. And when we IPO-ed, they were like, oh, you're never going to do that again. It was just a one-off. And then they came back and did it 5 more times with us, and then they did it across the industry. And the argument continues, oh, they're just going to pull it back. And that doesn't really -- those 2 things, right? It doesn't really match with the fact pattern, right? They build data centers and they could have pulled those back, but they didn't, right?

另一方面的因素在于这些公司，他们与我们签订了合同。在我们 IPO 时，他们的反应是，哦，你们再也不会这么做了，这只是一锤子买卖。但随后他们又回来与我们合作了 5 次，接着又将这种模式推广到了整个行业。现在仍有论调认为，哦，他们迟早会撤回这些业务的。但这其实——这两件事，对吧？这与事实的发展轨迹并不吻合，不是吗？他们建设了数据中心，本可以将其撤回，但他们并没有，对吧？。
They go through these periods where they build their own data centers and then they go through these periods where they go to third-party data center providers. So that's one thing. We do not believe that they are going to pull back, right? We just don't think that, that is the way that it's going to play out. But the second piece of it is what these contracts did for us was provide us with time, right? And with that time, you have seen us build a cloud that is specifically built to be able to support AI use cases. And with the software stacks, with the infrastructure, with the reputation for delivering this incredibly high-quality product, we have begun to win a broader and broader universe of clients.

他们会经历自建数据中心的周期，随后又会进入依赖第三方数据中心提供商的阶段。这是其一。我们认为他们不会缩减投入，对吧？我们根本不认为局势会朝那个方向发展。但其二，这些合同为我们争取到了宝贵的时间，对吧？利用这段时间，大家有目共睹，我们打造了一个专为支持 AI 应用场景而生的云平台。凭借卓越的 software stacks 和基础设施，以及交付顶尖高质量产品所积累的声誉，我们已经开始赢得越来越庞大的客户群体。
And so some of those contracts may come back to us. Some of those contracts may not. But the size and scale of the business, our ability to support enterprise, our ability to support governments, our ability to support our own products internally, our managed inference product, all of those things, those internal demand things, those are incredible paths to building a sustainable cloud. And we believe that is a necessary part of exiting this period of disequilibrium in a way that allows you to be successful and a hyperscale provider of the infrastructure that is required by the world for artificial intelligence. And we're really well positioned to do that.

因此，部分合同或许会失而复得。部分则不然。然而，凭借庞大的业务规模与体量，加之我们为企业、政府以及内部自有产品提供支持的能力，还有我们的 managed inference 产品，所有这一切，尤其是内部需求，为打造可持续的 cloud 开辟了可靠路径。我们坚信，要想顺利度过当前的失衡期，并成功蜕变为全球 artificial intelligence 基础设施的 hyperscale 提供商，这些都是必经之路。而在这方面，我们已经占据了得天独厚的优势。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Let's talk about building the cloud. So there are a number of pieces that I think are interesting. We could talk about managed inference, for example. There's a CPU pull-through piece to this as observability. Maybe just take a step back for us. What are the pieces that you think are most strategic to going from AI neo-cloud to full-blown long-term hyperscaler winner?

我们来探讨一下 cloud 的建设。我认为其中有几个环节非常值得关注。比如，我们可以聊聊 managed inference。这其中不仅涉及 CPU pullthrough 效应，还牵涉到 observability。也许我们可以先退一步来看全局。要从一家 AI neocloud 蜕变为真正成熟且长盛不衰的 hyperscaler 赢家，你认为哪些环节最具战略意义？.
Michael Intrator Co-founder, President, CEO & Chairman

So the answer to that is we meet our clients where they are, right? And so when we go and we work with the client, they tell us what they want, right? And we can be extremely flexible about integrating, hey, we've got this particular type of storage we want to use. Okay, we'll build it into our system, not a big deal. So like it really depends on who the client is, what the workload they're trying to support will define what we bring to market. The attach rates, and I think I spoke about this maybe 2 earnings ago, like 75% of our clients are using 3 different services, right? 3 different silos within our product suite are already being consumed, right? That's exactly what you want as you're building the cloud. That is exactly the way that you measure how people are going to consume what you're doing.

因此，这个问题的答案在于，我们会立足于客户的实际现状来提供服务。在与客户合作的过程中，他们会明确提出自己的需求。我们在系统整合方面具备极高的灵活性，如果客户提出想要使用某种特定的 storage，没问题，我们可以将其接入我们的系统，这并非难事。归根结底，这完全取决于客户的身份；他们需要支持何种 workload，决定了我们会向市场推出怎样的产品。至于 attach rates，我记得大概在两次 earnings 之前就曾提及，目前我们有75%的客户正在使用三种不同的服务。也就是说，我们产品矩阵中的三个不同 silos 已经被客户实际采用。这正是你在构建 cloud 业务时最期望看到的局面，同时也正是你用来衡量市场将如何使用你所提供服务的准确方式。
And I would argue that the percentages are even higher than what they look like because some of our clients are these really, really early-stage ventures that are not up to product # 2 and product #3 yet. They're still kind of like working it out. And so we really think that your -- you've got to build a suite of software services, whether it's storage or memory or networking and all the different things that people are going to consume and then go ahead and put it in front of them and say, look, we can help you build your company. We can help you deliver your service. We can help you be successful because of the infrastructure that you are going to be able to run your products on. And that has been an engine for us.

而且我认为，实际的比例甚至比表面数据更高，因为我们有部分客户是非常早期的初创企业，他们甚至还没开发出第二或第三款产品，仍处于摸索阶段。因此我们坚信，你必须打造出一整套 software services——无论是 storage、memory 还是 networking，以及客户将会使用的各种功能——然后将这些服务提供给他们，并告诉他们：看，我们能帮你打造公司。我们能帮你交付服务。我们能助你走向成功，因为你可以在我们的 infrastructure 上运行你的产品。这一直是我们不断发展的动力引擎。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Absolutely. In terms of road map, anything you can share on where customers are pulling next?

当然。就产品路线图而言，关于客户接下来的需求动向，您有什么可以透露的吗？。
Michael Intrator Co-founder, President, CEO & Chairman

We are -- we've always talked about the fact that we are client-led, right? And being client-led means that you spend time with your important clients and you talk to them about what they're trying to accomplish and you let them kind of help you build your products. So a lot of the storage solutions that we have were built specifically to help folks that had a very specific problem. When you look at the way that our road map has led us internationally, right, to ensure that we are both resilient from a capacity factor, but also able to serve different markets with low latency infrastructure.

我们是——我们始终强调自身 clientled 的定位，对吧？所谓 clientled，意味着你需要投入时间与核心客户沟通，了解他们的目标，并让他们参与到产品的研发中来。因此，我们目前的许多 storage solutions，都是为解决客户的特定痛点而量身定制的。当你审视我们的 road map 引导我们走向国际化的方式时，对吧，其核心目的不仅在于确保我们在 capacity factor 方面具备足够的韧性，同时也是为了能够依托 low latency infrastructure，更好地服务于各个不同的市场。
I mean like all of those things are really manifestations of our clients and what they need, and that really does inform the road map. I mean sitting at the center of the flywheel, having the conversations with all of these incredible entrepreneurs or existing companies that are integrating artificial intelligence into their workflows. And that is really, really fascinating, right? So just absolutely fascinating to see how that works.

说到底，这一切其实都是客户及其需求的具象体现，这也切实地指引了我们的发展路线图。置身于飞轮的中心，我们得以与那些了不起的创业者，或是正将人工智能整合进自身工作流的成熟企业展开对话。这确实令人无比着迷，不是吗？亲眼目睹这一切的运作方式，绝对是一件极具吸引力的事。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Maybe the perfect case study is actually someone like a Caterpillar, which you were talking about earlier. Give us a sense for the flavor of the enterprise customer conversations that you're having today where customers will say, look, we have previously used 1 of 3 hyperscalers. And we're now incrementally moving net new workloads or even brownfield workloads over to CoreWeave. What does that look like in practice?

也许最完美的案例正是你早前提到的 Caterpillar。能否向我们描述一下，你们目前与企业客户的交流大概是怎样的情形？比如客户会表示，我们以前使用的是三大 hyperscalers 之一。而现在，我们正逐步将 net new workloads 甚至 brownfield workloads 迁移至 CoreWeave。这种转变在实际操作中究竟是怎样的？。
Michael Intrator Co-founder, President, CEO & Chairman

So what it looks like is when we bring a customer like that over, we try to wrap our arms around them and support them through the process, right? And so it really depends on who the customer is and what they're trying to build and what they're trying -- and we try to make it so that all of their resources are being focused on integrating AI to make their company better, faster, stronger, whatever -- however you want to talk about it.

因此，实际情况是，当我们引入这类客户时，我们会提供全方位的贴身服务，在整个流程中为他们保驾护航，对吧？这完全取决于客户的背景以及他们想要构建的愿景——我们的目标是，确保他们能将所有资源都集中在整合 AI 上，从而让企业变得更好、更快、更强，或者达到任何你所能想到的提升效果。
What we really are trying to do is simplify the process of ensuring that they have the most performant infrastructure to be able to train internal models, right, that they're able to serve their inference calls effectively. All of those pieces have to come together for us to be viewed as a viable alternative to one of the hyperscalers. And so the breadth of the services, like it is -- it's not endless, right? We really do say, hey, this is our lane and our lane is to be able to serve all the components that are required to drive artificial intelligence. And then we don't wander too far from it, right? Like the world doesn't need another solution for X, Y and Z. What it needs is the best solution for the AI workflow, and that's where we're focusing our energy.

我们真正的目标是化繁为简，确保客户拥有性能最强大的 infrastructure 来训练内部 models，并能高效地处理其 inference calls。只有将所有这些环节融为一体，我们才能真正成为足以替代那些 hyperscalers 的可靠选择。因此，我们提供的服务范围并非漫无边际，对吧？我们非常明确地表示，嘿，这是我们的专属赛道，而我们的核心任务就是提供驱动 artificial intelligence 所需的全套组件。我们绝不会偏离这一主业太远，对吧？毕竟，这个世界不需要在 X, Y and Z 领域再多出一个平庸的解决方案。市场真正渴求的是专为 AI workflow 打造的最优解，而这正是我们全力以赴的方向。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Mike, you've already touched on the diversity of your customer base. Do you have a view or do you -- how do you think about the mix between frontier models and open source, open weights? Does that have a second derivative impact either on the health of your customer base or the health of your business?

Mike，您刚才已经谈到了客户群体的多样性。对于 frontier models 与 open source、open weights 之间的组合比例，您有何看法？这种结构是否会对您客户群的良性发展，或是整体业务的稳健性产生 second derivative impact？。
Michael Intrator Co-founder, President, CEO & Chairman

So we're in a position -- when we think about like closed source versus open source, believing that this is not going to be a binary breakdown, right? There are going to be use cases for open source. There are going to be use cases for closed source. As a supplier of the cloud that is required to run these use cases regardless of whether it's open or closed, we're sort of indifferent, right? We want to make sure that our infrastructure is able to serve both sides of that fence equally well, equally as efficiently. And that's sort of how we've approached the problem.

因此，我们的立场是 当我们审视 closed source 与 open source 的对比时，我们认为这不会是一种非黑即白的二元对立，对吧？open source 会有其适用的 use cases。closed source 也会有其适用的 use cases。作为支撑这些 use cases 运行的 cloud 供应商，无论采用的是 open 还是 closed 模式，我们其实都一视同仁，对吧？我们希望确保自身的 infrastructure 能够同等优质、同等高效地服务于这两大阵营。这基本上就是我们应对这一问题的思路。
I think there are other people that have to spend more time deciding which models are appropriate for which workflows within their organization. But for us, it's the idea that we will provide the computing power that you need in order to be successful regardless of how you choose to allocate the infrastructure in terms of whether it's open source or closed source model. So we're sort of a cop-out, but we're sort of indifferent on that, right? Like it's just more demand for compute is better for our business.

我认为，其他人需要花更多时间去权衡，究竟哪种 models 才最契合其企业内部的 workflows。但对我们而言，核心理念在于：无论客户在部署 infrastructure 时是选择 open source 还是 closed source model，我们都会为其提供成功所需的 computing power。这种说法听起来或许有些避重就轻，但我们对此确实持中立态度，不是吗？毕竟，只要市场对 compute 的需求不断增长，我们的业务就会蒸蒸日上。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

The other part of the strategy that I wanted to ask you about is the relationship with NVIDIA on selling through pieces of software. Maybe bring us up to speed on some of your ability to take proprietary CoreWeave software and sell it outside of the immediate CoreWeave stack.

关于公司战略，我还想请教的另一部分是你们与 NVIDIA 在软件销售方面的合作关系。能否向我们介绍一下最新进展，即你们如何将 CoreWeave 的专有软件，推向 CoreWeave 核心技术栈以外的市场进行销售。
Michael Intrator Co-founder, President, CEO & Chairman

Yes. That was pretty cool. Yes, it was. It really was. We -- NVIDIA designated our software stack as a reference architecture. And that's super exciting for us because it really is a recognition of the quality of the solutions that we have built, right? And we're -- that was great. We had some really excited engineers that have put their blood, sweat and tears into building the infrastructure. And so it was a wonderful recognition that they thought the quality of what we have built is high enough to be designated a reference architecture. And so that was really great.

是的。那确实非常酷。是的，确实如此。真的是这样。我们——NVIDIA将我们的软件栈指定为参考架构。这令我们无比振奋，因为这无疑是对我们打造的解决方案质量的高度认可，不是吗？而我们——这真的太棒了。我们的工程师们对此激动万分，他们在构建这些基础设施时倾注了无数的心血与汗水。因此，对方认为我们的产品质量过硬，足以被指定为参考架构，这是一种莫大的肯定。这一切真的非常棒。
What it means in reality is that the ability to provide third parties access to our software solution on their infrastructure allows us to get some leverage on other balance sheets. And that's a great thing, right? Like we can go into companies that want to own their own infrastructure, and we can provide them a software layer. It's called Omni is what we call it. But it also allows us to build infrastructure in jurisdictions that we maybe are not comfortable owning or delivering an asset-heavy solution to for whatever reason. And once again, that's a great way to make use of other entities' ability to take the risk around the physical infrastructure while still being able to generate returns and to expand our TAM for the products that we bring to market. And so that's been a very exciting part of our portfolio. We closed a deal on that a couple of months ago, and there's a whole bunch coming down the pipe that really look like that for various reasons why we would use that model instead.

实际上，这意味着通过让第三方在其自身的基础设施上使用我们的软件解决方案，我们能够借助他人的资产负债表来发挥杠杆作用。这无疑是一大优势，不是吗？比如，对于那些希望拥有自有基础设施的公司，我们可以为其提供软件层。我们将其称之为 Omni。同时，这也让我们得以在某些特定的管辖区内进行基础设施布局，出于种种原因，我们可能并不愿意在这些地区持有资产或提供重资产解决方案。同样，这也是一种绝佳的策略：利用其他实体承担实体基础设施风险的能力，我们不仅能继续创造回报，还能扩大我们推向市场的产品的 TAM。因此，这已成为我们业务版图中极具前景的一部分。几个月前，我们刚刚敲定了一笔此类交易，而且目前还有大量类似的项目正在筹备中，这正是我们出于各种考量而选择采用这种模式的原因。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

I want to spend a couple of minutes here on capital structure because the appetite of the debt markets to own neo-cloud businesses ebbs and flows over time. Tell us a little bit about your plans for capital raising. How do you think about the optimal balance sheet structure for a company like CoreWeave?

我想在这里花几分钟探讨一下资本结构，因为债务市场对 neocloud 企业的投资意愿总是随时间起伏。能否向我们透露一下你们的融资计划？对于 CoreWeave 这样的公司而言，你认为最理想的资产负债表结构是怎样的？。
Michael Intrator Co-founder, President, CEO & Chairman

Yes. Look, we took a strategy around building our company that is, in many ways, part and parcel for how you go about or how the world has historically gone about building infrastructure and capital-intensive business, right? If you're SpaceX and you're valued at $2 trillion and you can sell some equity, you sell some equity and you can go ahead and build whatever you need to build because $2 trillion is a lot. But if you're building organically, like we were, the question is, how do you raise the capital to build at a scale that allows you to be of relevance. And the answer to that was clearly the debt markets. And I think that the market struggles to understand what we have done in the debt markets.

是的。你看，我们在企业发展上采取的战略，在很大程度上，与当今乃至历史上全球建设基础设施和资本密集型企业的必经之路并无二致，对吧？如果你是 SpaceX，估值高达2万亿美元，你可以通过出让部分股权来融资；只要卖掉一点股份，你就能放手去建设任何需要的项目，毕竟2万亿美元是一笔巨款。但如果你像我们一样，走的是内生性增长的道路，问题就变成了：你该如何筹集到足够的资金，从而将业务规模做大到足以具备行业影响力？对此，我们的答案很明确：求助于债务市场。而我认为，外界市场很难理解我们在债务市场上的这番操作。
And the largest engine of our borrowing is occurring at an SPV level, where we are providing transparency through to the credit of the offtake. And that is why we were able to build structures that allowed the credit market to underwrite what we were doing because they were basically looking through and saying, okay, it's Microsoft on the other side of this transaction. The money is going to flow into the SPV and then pay back the debt before it goes back to CoreWeave. And that was an incredibly effective engine for raising capital at an order of magnitude that has rarely ever been done by a company as new to the market as CoreWeave. That was a wonderful way of enabling us to drive the scale that we needed to be able to serve our clients.

我们最大的债务融资引擎在 SPV 层面运作，在此我们提供了极高的透明度，使外界能够直接穿透并看清 offtake 的信用状况。正因如此，我们才得以搭建起相应的架构，让信贷市场愿意为我们的业务提供承销，因为他们基本上能看透底层逻辑并认为，好的，这笔交易的另一方是 Microsoft。资金将先流入 SPV，用于偿还债务，随后才会流回 CoreWeave。事实证明，这是一个极其高效的融资引擎，其筹资规模之大，对于 CoreWeave 这样初入市场的公司而言实属罕见。这种绝佳的模式赋能我们实现了所需的业务规模，从而能够更好地为客户提供服务。
We also raised some debt at the ParentCo. We raised convertibles up at the ParentCo. We have a very -- not a lot of religion around this stuff, right? Like we look at the space and say, what is the most effective way, the cheapest way, to raise the best possible capital to be able to execute on our road map. And that has been the defining North Star around the capital market structures that we use. And we have been the tip of the spear around the innovation. We did the first GPU transaction. The -- just kind of looking back in history, the last debt structure we did was the first time anybody has been willing to take -- or any of the lenders have been willing to take renewal risk.

我们还在 ParentCo 进行了一些债务融资。我们在 ParentCo 发行了可转债。对于这类操作，我们并没有什么——并没有什么刻板的教条，对吧？我们会审视整个市场并思考：要筹集最优质的资金来推进我们的路线图，最有效、成本最低的方式是什么？这一直是我们构建资本市场结构时最核心的指引。在创新方面，我们始终走在最前沿。我们完成了首笔 GPU 交易。回顾过去的历程，我们上一次设计的债务结构，是市场上首次有人——或者说首次有贷款方——愿意承担续约风险。
Like that's an important step forward to being able to access capital markets to be able to take advantage of the short-term contracts because now the lenders are taking renewal risk. The one before that, we borrowed -- we were able to get the [ venture rated ] so that we were able to borrow at A- credit, like that's unbelievable, right, to be able to borrow for a company like us to be able to borrow at such a low cost of capital was kind of a crowning event within the group that builds these capital structures. It was incredible. And so it puts our borrowing really at par or close to at par with many of the hyperscalers that are out there raising capital, and that allows us to operate more effectively, more competitively.

能够进入资本市场并利用短期合同，是我们向前迈出的重要一步，因为如今是由贷款方来承担续约风险。在此之前的融资中，我们成功获得了 [ venture rated ]，从而能够以 A credit 的信用级别进行借款。这简直令人难以置信，像我们这样的公司能以如此低的资本成本获得融资，对于负责构建这些资本结构的团队而言，无疑是一个极具标志性的高光时刻。这确实非常了不起。这也使得我们的借款条件实际上已经与市场上许多正在融资的 hyperscalers 持平或接近持平，从而让我们能够以更高效率和更强竞争力开展运营。
Gabriela Borges Goldman Sachs Group, Inc., Research Division

Mike, congrats on all the milestones. Please join me in thanking Mike for his time.

Mike，祝贺您达成各项里程碑。请大家和我一起感谢 Mike 抽出宝贵时间。