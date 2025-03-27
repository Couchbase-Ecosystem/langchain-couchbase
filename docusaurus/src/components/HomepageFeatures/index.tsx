import React from 'react';
import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Vector Storage',
    description: (
      <>
        Use Couchbase as a vector store for LangChain with the <code>CouchbaseVectorStore</code> class.
      </>
    ),
  },
  {
    title: 'Caching',
    description: (
      <>
        Enhance your LLM applications with <code>CouchbaseCache</code> and <code>CouchbaseSemanticCache</code> for efficient caching.
      </>
    ),
  },
  {
    title: 'Chat History',
    description: (
      <>
        Store and retrieve chat message history with <code>CouchbaseChatMessageHistory</code> for seamless conversations.
      </>
    ),
  },
];

function Feature({title, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
