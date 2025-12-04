'use client'

import Badge from "@/components/badge"
import Card from "@/components/card"
import Carousel from "@/components/carousel"
import SlideEffect from "@/components/slide-effect"
import Image from "next/image"

const settings = {
  badge: {
    number: 1,
    text: 'get started in seconds',
  },
  title: 'Set Up in Minutes',
  description: 'Simply log in to your social media accounts through Gemnar, pick your favorite platforms, and start scheduling posts instantly. Gemnar is the plug-and-play tool for creators who value time and simplicity.',
  card_1: {
    title: 'Effortless Setup',
    content: 'Gemnar provides seamless account connections, guides, and built-in support for the most popular social networks, so you can start scheduling posts and managing content in no time.',
    carousel_images: [
      '/social-icons/1.svg',
      '/social-icons/2.svg',
      '/social-icons/3.svg',
      '/social-icons/4.svg',
      '/social-icons/5.svg',
    ]
  },
  card_2: {
    title: 'Manage Multiple Accounts',
    content: 'Running several profiles? Gemnar lets you manage all your social accounts from one place. Switch easily between profiles, plan ahead, and stay on top of your content flow at all times.'
  },
  card_3: {
    title: 'Works Anywhere',
    content: 'Gemnar is built as a mobile-first app — it works perfectly on phones, tablets, and desktops. Access your dashboard anywhere, create posts on the go, and keep your schedule rolling.'
  },
  card_4: {
    title: 'Privacy-Friendly by Design',
    content: 'Gemnar never uses your access tokens or connected accounts for any unauthorized or harmful purpose. Your data remains encrypted, secure, and private — always under your control.',
    image: 'https://framerusercontent.com/images/6jTglLZFhLYMIuOe7EC0QFeykU.png?scale-down-to=512',
  },
}

export default function Features1() {
  return (
    <div id='features' className="space-y-6 sm:space-y-7 md:space-y-8 lg:space-y-10 mx-auto text-center">
      {/* Badge */}
      <SlideEffect>
        <Badge number={settings.badge.number} text={settings.badge.text} />
      </SlideEffect>

      {/* Title */}
      <SlideEffect>
        <h2 className="text-2xl md:text-4xl lg:text-header capitalize font-medium leading-none text-transparent bg-clip-text bg-gradient-to-b from-black to-black/60 dark:from-white dark:to-white/60">{settings.title}</h2>
      </SlideEffect>

      {/* Description */}
      <SlideEffect className="px-2 sm:px-10 md:px-0 w-full md:max-w-3/4 mx-auto text-sm lg:text-base">{settings.description}</SlideEffect>

      {/* Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* card 1 */}
        <SlideEffect direction="right" className="col-span-1 lg:col-span-3 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">{settings.card_1.title}</h3>
            <p className="mb-4">{settings.card_1.content}</p>
            <Carousel images={settings.card_1.carousel_images} />
          </Card>
        </SlideEffect>

        {/* card 2 */}
        <SlideEffect direction="left" duration={1.3} className="col-span-1 lg:col-span-2 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">{settings.card_2.title}</h3>
            <p>{settings.card_2.content}</p>
          </Card>
        </SlideEffect>

        {/* card 3 */}
        <SlideEffect direction="right" duration={1} className="col-span-1 lg:col-span-2 h-full" isSpring={false}>
          <Card>
            <h3 className="text-xl md:text-title text-black dark:text-white font-medium">{settings.card_3.title}</h3>
            <p>{settings.card_3.content}</p>
          </Card>
        </SlideEffect>

        {/* card 4 */}
        <SlideEffect direction="left" className="col-span-1 lg:col-span-3 h-full" isSpring={false}>
          <Card className="flex flex-col lg:flex-row justify-center items-center">
            <div className="space-y-3 md:space-y-5">
              <h3 className="text-xl md:text-title text-black dark:text-white font-medium">{settings.card_4.title}</h3>
              <p>{settings.card_4.content}</p>
            </div>

            <Image className="w-32 my-auto mx-auto" src={settings.card_4.image} alt={settings.card_4.title} width={512} height={512} />
          </Card>
        </SlideEffect>
      </div>
    </div>
  )
}
