"""Models, validation-only calibration, and common metrics."""
import numpy as np
from scipy.special import expit,logit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score,log_loss,brier_score_loss
from sklearn.calibration import calibration_curve
from lightgbm import LGBMClassifier


class Estimator:
    def __init__(self,features,family='logistic',C=.1,trees=100,leaves=7):
        self.features,self.family,self.C,self.trees,self.leaves=features,family,C,trees,leaves
    def fit(self,frame):
        if self.family=='logistic':
            self.model=make_pipeline(StandardScaler(),LogisticRegression(C=self.C,max_iter=1000,random_state=42))
        elif self.family=='lightgbm':
            self.model=LGBMClassifier(n_estimators=self.trees,num_leaves=self.leaves,learning_rate=.03,
                min_child_samples=50,reg_lambda=5.,random_state=42,n_jobs=1,verbosity=-1,deterministic=True,force_col_wise=True)
        else:raise ValueError(self.family)
        self.model.fit(frame[self.features].to_numpy(dtype=float),frame.target.to_numpy())
        return self
    def predict(self,frame):
        return np.clip(self.model.predict_proba(frame[self.features].to_numpy(dtype=float))[:,1],1e-6,1-1e-6)


class Calibration:
    def __init__(self,method='none'):self.method=method
    def fit(self,p,y):
        x=logit(np.clip(p,1e-6,1-1e-6))
        if self.method=='platt':self.model=LogisticRegression(C=1e6,max_iter=1000).fit(x.reshape(-1,1),y)
        elif self.method=='isotonic':self.model=IsotonicRegression(out_of_bounds='clip').fit(p,y)
        return self
    def predict(self,p):
        if self.method=='platt':p=self.model.predict_proba(logit(np.clip(p,1e-6,1-1e-6)).reshape(-1,1))[:,1]
        elif self.method=='isotonic':p=self.model.predict(p)
        return np.clip(p,1e-6,1-1e-6)


def score(y,p):
    return {'games':len(y),'accuracy':float(accuracy_score(y,np.asarray(p)>=.5)),
            'log_loss':float(log_loss(y,p,labels=[0,1])),'brier':float(brier_score_loss(y,p))}


def folds(frame):
    return [y for y in range(2019,2025) if (frame.year<y).sum()>=500 and (frame.year==y).sum()>=100]


def evaluate_spec(frame,spec):
    probabilities,targets,parts=[],[],[]
    for year in folds(frame):
        training,validation=frame[frame.year<year],frame[frame.year==year]
        model=Estimator(**spec).fit(training)
        p=model.predict(validation)
        probabilities.extend(p);targets.extend(validation.target)
        parts.append({'year':year,'train_games':len(training),**score(validation.target,p)})
    return {'pooled':score(np.array(targets),np.array(probabilities)),'folds':parts}


def calibrate(validation,p):
    if set(validation.year.unique())!={2025}:raise ValueError('Calibration is restricted to 2025')
    dates=sorted(validation.date.unique())
    cutoff=dates[int(len(dates)*.7)]
    fit=validation.date.to_numpy()<cutoff
    choices={}
    for method in ['none','platt','isotonic']:
        model=Calibration(method).fit(p[fit],validation.target.to_numpy()[fit])
        choices[method]=score(validation.target.to_numpy()[~fit],model.predict(p[~fit]))
    selected=min(choices,key=lambda key:choices[key]['log_loss'])
    model=Calibration(selected).fit(p,validation.target.to_numpy())
    return model,{'selected':selected,'selection_scores':choices,'fit_end_exclusive':str(cutoff),
                  'selection_games':int((~fit).sum()),'policy':'refit selected calibrator on all 2025 for 2026 only'},fit


def intervals(frame,y,p,baseline):
    y=np.asarray(y);p=np.clip(p,1e-6,1-1e-6);baseline=np.clip(baseline,1e-6,1-1e-6)
    def loss(q):return -(y*np.log(q)+(1-y)*np.log1p(-q))
    diffs=np.column_stack([((p>=.5)==y).astype(float)-((baseline>=.5)==y).astype(float),
                           loss(baseline)-loss(p),(y-baseline)**2-(y-p)**2])
    dates=frame.date.dt.floor('D').to_numpy()
    sums=np.array([np.r_[diffs[dates==day].sum(axis=0),(dates==day).sum()] for day in np.unique(dates)])
    rng=np.random.default_rng(42)
    samples=sums[rng.integers(0,len(sums),size=(2000,len(sums)))].sum(axis=1)
    delta=samples[:,:3]/samples[:,3,None]
    return {name:np.quantile(delta[:,i],[.025,.975]).tolist() for i,name in enumerate(['accuracy_delta','log_loss_improvement','brier_improvement'])}


def plot_calibration(y,predictions,path,title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(6.5,5))
    ax.plot([0,1],[0,1],'--',color='gray',label='Perfect calibration')
    for name,p in predictions.items():
        actual,predicted=calibration_curve(y,p,n_bins=10,strategy='quantile')
        ax.plot(predicted,actual,'o-',label=name,markersize=4)
    ax.set(xlabel='Predicted blue-side win probability',ylabel='Observed win fraction',title=title,xlim=(0,1),ylim=(0,1))
    ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)
