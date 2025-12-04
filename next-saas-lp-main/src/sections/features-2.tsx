'use client'

import Badge from "@/components/badge"
import Card from "@/components/card"
import FadeEffect from "@/components/fade-effect"
import SlideEffect from "@/components/slide-effect"
import Image from "next/image"

const settings = {
  badge: {
    number: 2,
    text: 'PROMPTING INSIGHTS',
  },
  title: 'Get Inspired by Other Creators',
  description:
    'Discover how top creators craft their ideas. Explore prompts, extract keywords, and browse real content made by others - to spark your next big idea.',
  card_1: {
    title: 'Read Prompts. Extract Keywords.',
    content:
      'Dive into other creators prompts and uncover the key themes, styles, and keywords behind their viral content. Learn what works and why.',
    image: '/keywords.svg',
  },
  card_2: {
    title: 'Filter & Explore Creator Content',
    content:
      'Easily filter through videos and images made by creators. Sort by category, platform, or trend to find inspiration tailored to your brand or niche.',
    image:
      'https://framerusercontent.com/images/A718dQKmWnJEhhnu0SJfCGxzDM.svg', // Replace with something relevant (optional)
  },
}

export default function Features2() {
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1 */}
        <SlideEffect direction="right" className="col-span-1 h-full" isSpring={false}>
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

        {/* Card 2 */}
        <SlideEffect direction="left" duration={1.3} className="col-span-1 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">
              {settings.card_2.title}
            </h3>
            <p>{settings.card_2.content}</p>
            <div className="relative">
              <Image
                src={settings.card_2.image}
                alt={settings.card_2.title}
                width={512}
                height={512}
              />
              <FadeEffect color="secondary" />
            </div>
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}
