import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className="hero hero--primary" style={{padding: '4rem 0'}}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div style={{marginTop: '2rem'}}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/user-guide/getting-started"
            style={{marginRight: '1rem'}}>
            User Guide
          </Link>
          <Link
            className="button button--info button--lg"
            to="/docs/developer/installation">
            Developer Docs
          </Link>
        </div>
      </div>
    </header>
  );
}

function HomepageFeatures() {
  return (
    <section style={{padding: '4rem 0'}}>
      <div className="container">
        <div className="row">
          <div className="col col--4">
            <div className="text--center padding-horiz--md">
              <h3>📚 User Documentation</h3>
              <p>
                Comprehensive guides for end users covering all features from chat to project management.
              </p>
              <Link to="/docs/user-guide/getting-started">
                Get Started →
              </Link>
            </div>
          </div>
          <div className="col col--4">
            <div className="text--center padding-horiz--md">
              <h3>🛠️ Developer Docs</h3>
              <p>
                Technical documentation for developers including architecture, setup, and API reference.
              </p>
              <Link to="/docs/developer/installation">
                Start Building →
              </Link>
            </div>
          </div>
          <div className="col col--4">
            <div className="text--center padding-horiz--md">
              <h3>🔌 API Reference</h3>
              <p>
                Complete API documentation with examples for integrating with Native Colab.
              </p>
              <Link to="/docs/api/overview">
                Explore API →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} Documentation`}
      description="Comprehensive documentation for Native Colab - Unified Collaboration Platform">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
