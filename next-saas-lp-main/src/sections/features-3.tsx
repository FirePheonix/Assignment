'use client'

import Badge from "@/components/badge"
import Card from "@/components/card"
import SlideEffect from "@/components/slide-effect"
import Image from "next/image"

const settings = {
  badge: {
    number: 3,
    text: 'ADVANCED ANALYTICS',
  },
  title: 'Dive Into the Details',
  description:
    'Manage all your social accounts from a single dashboard. Track engagement, compare performance across platforms, and optimize your content strategy with deep insights and analytics.',
  card_1: {
    title: 'Unified Dashboard',
    content:
      'Connect all your social media profiles and manage posts, messages, and insights from one clean, easy-to-use interface.',
    image: 'https://framerusercontent.com/images/3FWbibttHBsnge8Td2JRVbNo.svg',
  },
  card_2: {
    title: 'Cross-Platform Insights',
    content:
      'View detailed analytics across Instagram, TikTok, LinkedIn, and more. See what’s working and where to focus your energy.',
    image: 'https://framerusercontent.com/images/eaFbEnL3er77EwtTIiUEMgYTLnQ.svg',
  },
  card_3: {
    title: 'Social Media Management',
    content:
      'Streamline your entire social media workflow — from content creation and scheduling to publishing and performance tracking — all in one seamless flow.',
    image: 'https://framerusercontent.com/images/82g4S0XdXlaUWPtoLMLmaJhP1yc.svg',
  },
}

export default function Features3() {
  return (
    <div className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Badge */}
      <SlideEffect>
        <Badge number={settings.badge.number} text={settings.badge.text} />
      </SlideEffect>

      {/* Title */}
      <SlideEffect>
        <h2 className="text-2xl md:text-4xl lg:text-header capitalize text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60 font-medium leading-normal">
          {settings.title}
        </h2>
      </SlideEffect>

      {/* Description */}
      <SlideEffect className="px-2 sm:px-10 md:px-0 w-full md:max-w-3/4 mx-auto text-sm lg:text-base">
        {settings.description}
      </SlideEffect>

      {/* Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* card 1 */}
        <SlideEffect direction="top" className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_1.title}
            </h3>
            <p className="mb-4">{settings.card_1.content}</p>
            <Image
              src={settings.card_1.image}
              alt={settings.card_1.title}
              width={512}
              height={512}
            />
          </Card>
        </SlideEffect>

        {/* card 2 */}
        <SlideEffect direction="top" delay={0.2} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_2.title}
            </h3>
            <p>{settings.card_2.content}</p>
            <Image
              src={settings.card_2.image}
              alt={settings.card_2.title}
              width={512}
              height={512}
            />
          </Card>
        </SlideEffect>

        {/* card 3 */}
        <SlideEffect direction="top" delay={0.3} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_3.title}
            </h3>
            <p>{settings.card_3.content}</p>
            <Image
              src={settings.card_3.image}
              alt={settings.card_3.title}
              width={512}
              height={512}
            />
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}
