'use client'

import Badge from "@/components/badge"
import Card from "@/components/card"
import SlideEffect from "@/components/slide-effect"
import Spinner from "@/components/spinner"
import TextRevealEffect from "@/components/text-reveal-effect"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ChatMessagesDemo } from "@/components/chat-messages-demo"

const settings = {
  badge: {
    number: 5,
    text: 'CREATOR CONNECTIONS',
  },
  title: 'Meet. Match. Collaborate.',
  description:
    'Discover creators and brands that align with your goals. Build authentic partnerships, launch campaigns together, and grow faster through meaningful connections.',
  card_1: {
    title: 'Discover and Connect Instantly',
    content:
      'Explore a dynamic network of creators and brands. Search by niche, style, or audience to find perfect matches for your campaigns or collaborations - all in one simple, AI-powered space.',
    CTA: {
      content: 'Start 30-day free trial',
      href: '#',
    },
    labels: [
      'travel-brand.io',
      'creatorhouse.me',
      'beauty-hub.ai',
      'techcollab.com',
      'fashionflow.co',
      'wellnesswave.io',
      'vibestudio.app',
    ],
    avatars: [
      'https://avatar.iran.liara.run/public/38',
      'https://avatar.iran.liara.run/public/40',
      'https://avatar.iran.liara.run/public/22',
      'https://avatar.iran.liara.run/public/6',
      'https://avatar.iran.liara.run/public/12',
      'https://avatar.iran.liara.run/public/37',
      'https://avatar.iran.liara.run/public/35',
    ],
  },
  card_2: {
    title: 'Smart Matching for Better Partnerships',
    content:
      'Our platform uses AI to recommend creators and brands based on interests, engagement metrics, and audience alignment - so every connection feels natural and effective.',
  },
  card_3: {
    title: 'Collaborate and Track Effortlessly',
    content:
      'Chat, plan campaigns, and monitor results without switching tools. From the first hello to final analytics - manage your collaborations in one seamless workflow.',
  },
}

export default function Features5() {
  return (
    <div className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Badge */}
      <SlideEffect>
        <Badge number={settings.badge.number} text={settings.badge.text} />
      </SlideEffect>

      {/* Title */}
      <TextRevealEffect className="text-2xl md:text-4xl lg:text-header text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60 font-medium leading-normal">
        {settings.title}
      </TextRevealEffect>

      {/* Description */}
      <SlideEffect className="px-2 sm:px-10 md:px-0 w-full md:max-w-3/4 mx-auto text-sm lg:text-base">
        {settings.description}
      </SlideEffect>

      {/* Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* card 1 */}
        <SlideEffect direction="top" className="grid-cols-1 lg:col-span-2 h-full" isSpring={false}>
          <Card className="flex flex-col lg:flex-row justify-center items-center">
            <div className="space-y-3 md:space-y-5 flex-1">
              <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
                {settings.card_1.title}
              </h3>
              <p className="mb-8 lg:mb-16">{settings.card_1.content}</p>
              <Link href={settings.card_1.CTA.href}>
                <Button className="bg-accent">{settings.card_1.CTA.content}</Button>
              </Link>
            </div>

            <Spinner labels={settings.card_1.labels} avatars={settings.card_1.avatars} />
          </Card>
        </SlideEffect>

        {/* card 2 */}
        <SlideEffect direction="right" className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_2.title}
            </h3>
            <p>{settings.card_2.content}</p>
          </Card>
        </SlideEffect>

        {/* card 3 - Chat Demo */}
        <SlideEffect direction="left" delay={0.2} className="col-span-1 row-span-2 h-full" isSpring={false}>
          <Card className="h-full flex items-center justify-center p-4">
            <ChatMessagesDemo />
          </Card>
        </SlideEffect>

        {/* card 4 */}
        <SlideEffect direction="right" delay={0.3} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_3.title}
            </h3>
            <p>{settings.card_3.content}</p>
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}
